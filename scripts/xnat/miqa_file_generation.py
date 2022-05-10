import os
import re
import pathlib
import pandas as pd


def convert_qc_csv(
    filename: str, new_filename: str, log_dir: str, verbose: bool = False
):
    """Convert the old Girder QC CSV format to the new CSV format."""
    source_file = os.path.join(log_dir, filename)
    target_file = os.path.join(log_dir, new_filename)
    if not pathlib.Path(source_file).exists():
        if verbose:
            print(f"{source_file} does not exist.")
        return
    if not source_file.endswith(".csv"):
        if verbose:
            print(f"{source_file} is not a CSV file.")
        return
    df = pd.read_csv(source_file, dtype=str)
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
                f"{source_file} is not congruent with the old"
                f" MIQA import format. Expected columns {str(expected_columns)} but recieved {str(df.columns)}."
            )
        return

    project_name_pattern = re.compile("([a-z]+)_incoming")
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
    new_df.to_csv(target_file, index=False)
    if verbose:
        print(f"Wrote converted CSV to {target_file}.")
