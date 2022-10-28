import json
import numpy
import os
import re
import pathlib
import pandas as pd
from enum import Enum


project_name_pattern = re.compile("([a-z]+)_incoming")


class MIQAFileFormat(Enum):
    CSV = 0
    JSON = 1


MIQADecisionCodes = {
    "0": "Q?",
    "1": "U",
    "2": "UE",
    "3": "UN",
}

MIQA2CNSDecisionCodes = { MIQADecisionCodes[key] : int(key) for key in MIQADecisionCodes.keys() }

def get_data_from_old_format_file(file, verbose=False):
    if not pathlib.Path(file).exists():
        if verbose:
            print(f"{file} does not exist.")
        return
    if not file.endswith(".csv"):
        if verbose:
            print(f"{file} is not a CSV file.")
        return
    df = pd.read_csv(file, dtype=str)
    expected_columns = [
        "xnat_experiment_id",
        "nifti_folder",
        "scan_id",
        "scan_type",
        "experiment_note",
        "decision",
        "scan_note",
    ]
    if len(df.columns) != len(expected_columns) or any(df.columns != expected_columns):
        if verbose:
            print(
                f"{file} is not congruent with the old"
                f" MIQA import format. Expected columns {str(expected_columns)} but recieved {str(df.columns)}."
            )
        return None
    return df


def convert_json_to_check_new_sessions_df(
    json_dict: dict
) -> pd.DataFrame:
    
    dataframe_cols = ['xnat_experiment_id','nifti_folder','scan_id','scan_type','experiment_note','decision','scan_note']
    
    all_scans = []
    for project_name in json_dict['projects'].keys():
        experiments = json_dict['projects'][project_name]["experiments"]
        for xnat_experiment_id in experiments.keys():
            experiment =  experiments[xnat_experiment_id]
            for scan_name_id in experiment["scans"].keys():
                scan = experiment["scans"][scan_name_id]
                
                # initilize record
                data = {}
                for col in dataframe_cols:
                    data[col] = pd.NA
                
                # fill out fields
                data['xnat_experiment_id'] = xnat_experiment_id
                data['nifti_folder'] = re.sub(f"/{scan_name_id}/.*$", "", scan["frames"]["0"]["file_location"])
                data['scan_id'], _ = scan_name_id.split('_', maxsplit=1)
                data['scan_id'] = int(data['scan_id'])
                data['scan_type'] = scan["type"]
                
                if experiment["notes"] != None and experiment["notes"] != "":
                    data["experiment_note"] = experiment["notes"]
                
                if scan["last_decision"] != None:
                    data["decision"] = MIQA2CNSDecisionCodes[scan["last_decision"]["decision"]]
                    
                    if scan["last_decision"]["note"] != "":
                        data["scan_note"] = scan["last_decision"]["note"]

                df = pd.DataFrame.from_records([data], columns=dataframe_cols)
                all_scans.append(df)
                
    return pd.concat(all_scans, ignore_index=True)


def convert_dataframe_to_new_format(
    df,
    image_extensions,
    verbose=False,
    session=None,
    subject_mapping=None,
):
    new_rows = []
    for _index, row in df.iterrows():
        experiment = row["xnat_experiment_id"]

        if subject_mapping and experiment in subject_mapping:
            (subject_id, session_id, project_tmp) = subject_mapping[experiment]
            # match = project_name_pattern.search(row["nifti_folder"])
            #  project_name = match.group(1).upper()
            project_name = project_tmp.split("_")[0].upper()
        else:
            subject_id = ""
            session_id = ""
            project_name = "unknown"

        scan_type = row["scan_type"]
        scan_link = ""
        if session:
            scan_link = session.get_xnat_session_address(experiment)

        decision = (
            MIQADecisionCodes[row["decision"]]
            if row["decision"] in MIQADecisionCodes
            else ""
        )

        scan_dir = pathlib.Path(
            row["nifti_folder"], f"{row['scan_id']}_{row['scan_type']}"
        )
        frame_locations = [
            location
            for location in scan_dir.glob("*")
            if any(str(location).endswith(extension) for extension in image_extensions)
        ]
        if len(frame_locations) == 0 and verbose:
            print(
                f"Error:convert_dataframe_to_new_format:\n",
                f"    Could not find any image files under {scan_dir}. Failed to write any frames for this scan."
            )

        frame_locations.sort(key=lambda path: path.name)
        for index, frame_location in enumerate(frame_locations):
            # frame_number = row["scan_id"] if len(frame_locations) < 2 else index
            frame_number = index
            new_rows.append(
                [
                    project_name,  # project_name
                    experiment,  # experiment_name
                    # f"{experiment}_{scan_type}",  # scan_name
                    # Anne: does scan name have to be uniquelly defined across experiments as it was defined as
                    #  f"{experiment}_{scan_type}",
                    f"{row['scan_id']}_{row['scan_type']}",  # scan_name
                    scan_type,  # scan_type
                    frame_number,  # frame_number
                    str(frame_location),  # file_location
                    row["experiment_note"],  # experiment_notes
                    subject_id,  # subject_id
                    session_id,  # session_id
                    scan_link,  # scan_link
                    decision,  # last_decision
                    "",  # last_decision_creator
                    row["scan_note"],  # last_decision_note
                    "",  # last_decision_created
                    "",  # identified_artifacts
                    "",  # location_of_interest
                ]
            )
    new_df = pd.DataFrame(
        new_rows,
        columns=[
            "project_name",
            "experiment_name",
            "scan_name",
            "scan_type",
            "frame_number",
            "file_location",
            "experiment_notes",
            "subject_id",
            "session_id",
            "scan_link",
            "last_decision",
            "last_decision_creator",
            "last_decision_note",
            "last_decision_created",
            "identified_artifacts",
            "location_of_interest",
        ],
    )
    return new_df


def import_dataframe_to_dict(df, verbose=False):
    if df.empty and verbose:
        print("Import data is empty.")

    ingest_dict = {"projects": {}}
    for project_name, project_df in df.groupby("project_name"):
        project_dict = {"experiments": {}}
        if list(project_df["experiment_name"].unique()) != [""]:
            for experiment_name, experiment_df in project_df.groupby("experiment_name"):
                experiment_dict = {"scans": {}}
                if "experiment_notes" in experiment_df.columns:
                    experiment_dict["notes"] = experiment_df["experiment_notes"].iloc[0]
                for scan_name, scan_df in experiment_df.groupby("scan_name"):
                    scan_dict = {}
                    if list(scan_df["file_location"].unique()) != [""]:
                        try:
                            scan_dict = {
                                "type": scan_df["scan_type"].iloc[0],
                                "frames": {
                                    int(row[1]["frame_number"]): {
                                        "file_location": row[1]["file_location"]
                                    }
                                    for row in scan_df.iterrows()
                                },
                            }
                        except ValueError as e:
                            if verbose:
                                print(
                                    f'Invalid frame number {str(e).split(":")[-1]}. Must be an integer value.'
                                )

                        if "subject_id" in scan_df.columns:
                            scan_dict["subject_id"] = scan_df["subject_id"].iloc[0]
                        if "session_id" in scan_df.columns:
                            scan_dict["session_id"] = scan_df["session_id"].iloc[0]
                        if "scan_link" in scan_df.columns:
                            scan_dict["scan_link"] = scan_df["scan_link"].iloc[0]
                        if (
                            "last_decision" in scan_df.columns
                            and scan_df["last_decision"].iloc[0]
                        ):
                            decision_dict = {
                                "decision": scan_df["last_decision"].iloc[0],
                                "creator": scan_df["last_decision_creator"].iloc[0],
                                "note": scan_df["last_decision_note"].iloc[0],
                                "created": scan_df["last_decision_created"].iloc[0],
                                "user_identified_artifacts": scan_df[
                                    "identified_artifacts"
                                ].iloc[0]
                                or None,
                                "location": scan_df["location_of_interest"].iloc[0]
                                or None,
                            }
                            decision_dict = {
                                k: (v or None) for k, v in decision_dict.items()
                            }
                            scan_dict["last_decision"] = decision_dict
                        else:
                            scan_dict["last_decision"] = None

                        experiment_dict["scans"][scan_name] = scan_dict
                project_dict["experiments"][experiment_name] = experiment_dict
        ingest_dict["projects"][project_name] = project_dict
    return ingest_dict


def write_miqa_import_file(
    data_input: list,
    new_filename: str,
    log_dir: str,
    verbose: bool = False,
    format: MIQAFileFormat = MIQAFileFormat.CSV,
    session=None,
    subject_mapping=None,
    image_extensions: list = [".nii.gz", ".nii", ".nrrd"],
    project_list: list = [],
):
    """Convert the old Girder QC CSV format to the new CSV format."""
    target_file = os.path.join(log_dir, new_filename)

    if format == MIQAFileFormat.CSV:
        df = pd.DataFrame(
            columns=data_input[0].strip().split(","),
            data=[row.strip().replace("\"", "").split(",") for row in data_input[1:]]
        )
        new_df = convert_dataframe_to_new_format(
            df,
            image_extensions,
            verbose,
            session=session,
            subject_mapping=subject_mapping,
        )
        new_df = new_df.replace(numpy.nan, "", regex=True)

        non_empty_projects = new_df["project_name"].unique()
        for non_empty_project in non_empty_projects:
            if non_empty_project not in project_list:
                raise Exception(
                    f"Found data for {non_empty_project}, \
                        which was not included in {project_list}. \
                            Failed to write file."
                )
        for project_name in project_list:
            if project_name not in non_empty_projects:
                new_df.loc[len(new_df.index)] = [project_name] + [
                    "" for col in range(len(new_df.columns) - 1)
                ]
        new_df.to_csv(target_file, index=False)
        if verbose:
            print(f"Wrote converted CSV to {target_file}.")

    elif format == MIQAFileFormat.JSON:
        with open(target_file, "w") as fp:
            json.dump(data_input, fp)
        if verbose:
            print(f"Wrote converted JSON to {target_file}.")


def read_miqa_import_file(
    filename: str,
    log_dir: str,
    verbose: bool = False,
    format: MIQAFileFormat = MIQAFileFormat.CSV,
    image_extensions: list = [".nii.gz", ".nii", ".nrrd"],
):
    """Return a dictionary representing all scans in a MIQA CSV or JSON"""
    source_file = os.path.join(log_dir, filename)

    if format == MIQAFileFormat.CSV:
        df = get_data_from_old_format_file(source_file, verbose)
        if df is not None:
            new_df = convert_dataframe_to_new_format(df, image_extensions, verbose)
        else:
            new_df = convert_dataframe_to_new_format(
                pd.read_csv(source_file, dtype=str),
                image_extensions,
                verbose,
            )
        return import_dataframe_to_dict(new_df, verbose)
    elif format == MIQAFileFormat.JSON:
        return json.load(open(source_file))
