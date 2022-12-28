from dateutil.parser import parse
import json
import os
import re
import pathlib
import pandas as pd
from schema import Optional, Or, Schema, SchemaError, Use


project_name_pattern = re.compile("([a-z]+)_incoming")


MIQADecisionCodes = {
    "0": "Q?",
    "1": "U",
    "2": "UE",
    "3": "UN",
}

MIQA2CNSDecisionCodes = {MIQADecisionCodes[key]: int(key) for key in MIQADecisionCodes.keys()}


def convert_json_to_check_new_sessions_df(
    json_dict: dict
) -> pd.DataFrame:

    dataframe_cols = [
        'xnat_experiment_id',
        'nifti_folder',
        'scan_id',
        'scan_type',
        'experiment_note',
        'decision',
        'scan_note'
    ]

    all_scans = []
    for project_name in json_dict['projects'].keys():
        experiments = json_dict['projects'][project_name]["experiments"]
        for xnat_experiment_id in experiments.keys():
            experiment = experiments[xnat_experiment_id]
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

                if experiment["notes"] is not None and experiment["notes"] != "":
                    data["experiment_note"] = experiment["notes"]

                if ('last_decision' in scan.keys()) and  (scan["last_decision"] is not None):
                    data["decision"] = MIQA2CNSDecisionCodes[scan["last_decision"]["decision"]]

                    if scan["last_decision"]["note"] != "":
                        data["scan_note"] = scan["last_decision"]["note"]

                if "decisions" in scan and scan["decisions"] is not None and len(scan["decisions"]) > 0:
                    decisions = scan["decisions"]
                    decisions.sort(key=lambda x: parse(x["created"]))

                    data["decision"] = decisions[-1]["decision"]
                    data["scan_note"] = '; '.join([f'{d["creator"][:3]}: {d["note"]}' for d in decisions])

                df = pd.DataFrame.from_records([data], columns=dataframe_cols)
                all_scans.append(df)

    return pd.concat(all_scans, ignore_index=True)


def convert_dataframe_to_new_format(
    df,
    session=None,
    subject_mapping=None,
):
    new_rows = []
    for _index, row in df.iterrows():
        experiment = row["xnat_experiment_id"]

        if subject_mapping and experiment in subject_mapping:
            (subject_id, session_id, project_tmp) = subject_mapping[experiment]
            project_name = project_tmp.split("_")[0].upper()
        else:
            subject_id = ""
            session_id = ""
            project_name = "unknown"

        scan_type = row["scan_type"]
        scan_link = ""
        if session:
            scan_link = session.get_xnat_session_address(experiment)

        scan_note = ""
        decision = (
            MIQADecisionCodes[row["decision"]]
            if row["decision"] in MIQADecisionCodes
            else ""
        )
        if 'scan_note' in row:
            scan_note = row['scan_note'].replace('\"', '')

        scan_dir = pathlib.Path(
            row["nifti_folder"], f"{row['scan_id']}_{row['scan_type']}"
        )
        frame_locations = [
            location
            for location in scan_dir.glob("*.nii.gz")
        ]
        if len(frame_locations) == 0:
            raise Exception(
                f"Could not find any image files under {scan_dir}. Failed to write any frames for this scan."
            )

        frame_locations.sort(key=lambda path: path.name)
        for index, frame_location in enumerate(frame_locations):
            frame_number = index
            new_rows.append(
                [
                    project_name,  # project_name
                    experiment,  # experiment_name
                    f"{row['scan_id']}_{row['scan_type']}",  # scan_name
                    scan_type,  # scan_type
                    frame_number,  # frame_number
                    str(frame_location),  # file_location
                    row["experiment_note"].replace('\"', ''),  # experiment_notes
                    subject_id,  # subject_id
                    session_id,  # session_id
                    scan_link,  # scan_link
                    decision,  # last_decision
                    "",  # last_decision_creator
                    scan_note,  # last_decision_note
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


def import_dataframe_to_dict(df):
    if df.empty:
        return {}

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
                        scan_dict = {
                            "type": scan_df["scan_type"].iloc[0],
                            "frames": {
                                int(row[1]["frame_number"]): {
                                    "file_location": row[1]["file_location"]
                                }
                                for row in scan_df.iterrows()
                            },
                            "decisions": [],
                        }
                        if "subject_id" in scan_df.columns:
                            scan_dict["subject_id"] = scan_df["subject_id"].iloc[0]
                        if "session_id" in scan_df.columns:
                            scan_dict["session_id"] = scan_df["session_id"].iloc[0]
                        if "scan_link" in scan_df.columns:
                            scan_dict["scan_link"] = scan_df["scan_link"].iloc[0]
                        if "last_decision" in scan_df.columns and scan_df["last_decision"].iloc[0]:
                            decision_dict = {
                                "decision": scan_df["last_decision"].iloc[0],
                                "creator": scan_df["last_decision_creator"].iloc[0],
                                "note": scan_df["last_decision_note"].iloc[0],
                                "created": str(scan_df["last_decision_created"].iloc[0])
                                if scan_df["last_decision_created"].iloc[0]
                                else None,
                                "user_identified_artifacts": scan_df["identified_artifacts"].iloc[0]
                                or None,
                                "location": scan_df["location_of_interest"].iloc[0] or None,
                            }
                            decision_dict = {k: (v or None) for k, v in decision_dict.items()}
                            scan_dict["decisions"].append(decision_dict)

                        if "subject_ID" in scan_df.columns:
                            scan_dict["subject_ID"] = scan_df["subject_ID"].iloc[0]
                        if "session_ID" in scan_df.columns:
                            scan_dict["session_ID"] = scan_df["session_ID"].iloc[0]

                        experiment_dict["scans"][scan_name] = scan_dict
                project_dict["experiments"][experiment_name] = experiment_dict
        ingest_dict["projects"][project_name] = project_dict
    return ingest_dict


def validate_import_data(import_dict):
    import_schema = Schema(
        {
            'projects': {
                Optional(Use(str)): {
                    'experiments': {
                        Optional(Use(str)): {
                            Optional('notes'): Optional(str, None),
                            'scans': {
                                Optional(Use(str)): {
                                    'type': Use(str),
                                    Optional('subject_id'): Or(str, None),
                                    Optional('session_id'): Or(str, None),
                                    Optional('scan_link'): Or(str, None),
                                    'frames': {Use(int): {'file_location': Use(str)}},
                                    Optional('decisions'): [
                                        {
                                            'decision': Use(str),
                                            'creator': Or(str, None),
                                            'note': Or(str, None),
                                            'created': Or(str, None),
                                            'user_identified_artifacts': Or(str, None),
                                            'location': Or(str, None),
                                        },
                                    ],
                                    Optional('last_decision'): Or(
                                        {
                                            'decision': Use(str),
                                            'creator': Or(str, None),
                                            'note': Or(str, None),
                                            'created': Or(str, None),
                                            'user_identified_artifacts': Or(str, None),
                                            'location': Or(str, None),
                                        },
                                        None,
                                    ),
                                }
                            },
                        }
                    }
                }
            }
        }
    )
    try:
        import_schema.validate(import_dict)
    except SchemaError:
        return False
    return True


def write_miqa_import_file(
    data: {},
    filename: str,
    log_dir: str,
):
    """Write MIQA Import JSON from input dictionary"""

    if not validate_import_data(data):
        return False
    target_file = os.path.join(log_dir, filename)
    with open(target_file, "w") as fp:
        json.dump(data, fp)

    return True


def read_miqa_import_file(
    filename: str,
    log_dir: str,
):
    """Return a dictionary with MIQA Import JSON contents"""

    source_file = os.path.join(log_dir, filename)
    data = json.load(open(source_file))
    if not validate_import_data(data):
        return {}

    return data
