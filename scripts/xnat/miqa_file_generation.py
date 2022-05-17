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


def convert_dataframe_to_new_format(df, verbose=False):
    new_rows = []
    for _index, row in df.iterrows():
        match = project_name_pattern.search(row["nifti_folder"])
        if match:
            project_name = match.group(1).upper()
        else:
            project_name = "unknown"
        # last decision metadata is stored in the scan_note field like this:
        # "{note} {creator} {created}"
        try:
            scan_note = row["scan_note"].split(" ")
            note = " ".join(scan_note[:-3])
            creator = scan_note[-3]
            created = f"{scan_note[-2]} {scan_note[-1]}".strip()
            print(f"decomposed {scan_note} into [{note}, {creator}, {created}]")
        except Exception:
            # Use empty fields if the scan_note is not parseable
            note = ""
            creator = ""
            created = ""
        new_rows.append(
            [
                project_name,  # project_name
                row["xnat_experiment_id"],  # experiment_name
                f"{row['xnat_experiment_id']}_{row['scan_type']}",  # scan_name
                row["scan_type"],  # scan_type
                row["scan_id"],  # frame_number
                str(
                    pathlib.Path(
                        row["nifti_folder"],
                        f"{row['scan_id']}_{row['scan_type']}",
                        "image.nii.gz",
                    )
                ),  # file_location
                row["experiment_note"],  # experiment_notes
                # TODO populate these correctly
                "",  # subject_id
                "",  # session_id
                "",  # scan_link
                row["decision"],  # last_decision
                creator,  # last_decision_creator
                note,  # last_decision_note
                created,  # last_decision_created
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
        for experiment_name, experiment_df in project_df.groupby("experiment_name"):
            experiment_dict = {"scans": {}}
            if "experiment_notes" in experiment_df.columns:
                experiment_dict["notes"] = experiment_df["experiment_notes"].iloc[0]
            for scan_name, scan_df in experiment_df.groupby("scan_name"):
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
                        "location": scan_df["location_of_interest"].iloc[0] or None,
                    }
                    decision_dict = {k: (v or None) for k, v in decision_dict.items()}
                    scan_dict["last_decision"] = decision_dict
                else:
                    scan_dict["last_decision"] = None

                experiment_dict["scans"][scan_name] = scan_dict
            project_dict["experiments"][experiment_name] = experiment_dict
        ingest_dict["projects"][project_name] = project_dict
    return ingest_dict


def write_miqa_import_file(
    filename: str,
    new_filename: str,
    log_dir: str,
    verbose: bool = False,
    format: MIQAFileFormat = MIQAFileFormat.CSV,
):
    """Convert the old Girder QC CSV format to the new CSV format."""
    source_file = os.path.join(log_dir, filename)
    target_file = os.path.join(log_dir, new_filename)

    df = get_data_from_old_format_file(source_file, verbose)
    new_df = convert_dataframe_to_new_format(df, verbose)
    new_df.replace(numpy.nan, "", regex=True)

    if format == MIQAFileFormat.CSV:
        new_df.to_csv(target_file, index=False)
        if verbose:
            print(f"Wrote converted CSV to {target_file}.")
    elif format == MIQAFileFormat.JSON:
        ingest_dict = import_dataframe_to_dict(new_df, verbose)
        with open(new_filename, "w") as fp:
            json.dump(ingest_dict, fp)
        if verbose:
            print(f"Wrote converted JSON to {target_file}.")


def read_miqa_import_file(
    filename: str,
    log_dir: str,
    verbose: bool = False,
    format: MIQAFileFormat = MIQAFileFormat.CSV,
):
    """Return a dictionary representing all scans in a MIQA CSV or JSON"""
    source_file = os.path.join(log_dir, filename)

    if format == MIQAFileFormat.CSV:
        df = get_data_from_old_format_file(source_file, verbose)
        if df is not None:
            new_df = convert_dataframe_to_new_format(df, verbose)
        else:
            new_df = convert_dataframe_to_new_format(
                pd.read_csv(source_file, dtype=str),
                verbose,
            )
        return import_dataframe_to_dict(new_df, verbose)
    elif format == MIQAFileFormat.JSON:
        return json.load(open(source_file))
