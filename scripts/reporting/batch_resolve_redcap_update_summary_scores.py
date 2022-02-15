#!/usr/bin/env python
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import argparse
import pandas as pd
from pathlib import Path
import sibispy
import sibispy.cli
from sibispy import sibislogger as slog
import sys
from typing import Sequence, List, Dict, Mapping, Union
import yaml

import github
import pdb
from collections import defaultdict
import numpy as np

import batch_script_utils as utils


def run_batch(verbose, metadata):
    script_path = "/sibis-software/python-packages/sibispy/cmds/"
    events = ["Baseline", "1y", "2y", "3y", "4y", "5y", "6y", "7y"]
    update_scores_base_command = [
        script_path + "redcap_update_summary_scores.py",
        "-a",
        "-s",
    ]
    locking_data_base_command = [
        script_path + "exec_redcap_locking_data.py",
        "-e",
    ] + events

    title_string = "redcap_import_record:Failed to import into REDCap"
    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    scraped_tuples = []
    for issue in issues:
        if title_string in issue.title:
            for label in issue.get_labels():
                if "redcap_update_summary_scores" == label.name:
                    request_error = utils.rehydrate_issue_body(issue.body)[
                        "requestError"
                    ]
                    subject_ids = utils.extract_unique_subject_ids(request_error)
                    first_field = request_error.split('","')[1]
                    field_row = metadata[metadata["field_name"] == first_field]
                    form = field_row[
                        "form_name"
                    ].item()
                    instrument = field_row[
                        "instrument"
                    ].item()
                    
                    scraped_tuples.append((issue, subject_ids, form, instrument))
                    if verbose:
                        print(
                            f"\nFound the following subject id's in #{issue.number}:\n{subject_ids}"
                        )
                    break

    all_found_subject_ids = "\n".join(
        ["\n".join(subject_ids) for _, subject_ids, _, _ in scraped_tuples]
    )
    print(f"\nFound the following subject id's:\n{all_found_subject_ids}")
    if not utils.prompt_y_n("Are all subject id's valid? (y/n)"):
        print("Aborting")
        return

    for issue, subject_ids, form, instrument in scraped_tuples:
        print(
            f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nResolving issue #{issue.number} with the following id's:\n{subject_ids}\n"
        )

        # Loop through subject id's mentioned in issue since redcap_update_summary_scores.py only recalculates one at a time
        errors_recalculating = []
        errors_relocking = []
        for subject_id in subject_ids[:5]:
            if verbose:
                print(f"\nUnlocking {subject_id}...")
            unlock_command = (
                ["python"]
                + locking_data_base_command
                + ["-f"]
                + [form]
                + ["-s"]
                + [subject_id]
                + ["--unlock"]
            )
            completed_unlock_process = utils.run_command(unlock_command, verbose)

            if verbose:
                print(f"\nRecalculating {subject_id}...")
            recalculate_command = (
                ["python"] + update_scores_base_command + [subject_id] + ["-i"] + [instrument]
            )
            completed_recalculate_process = utils.run_command(
                recalculate_command, verbose
            )
            out = completed_recalculate_process.stdout
            err = completed_recalculate_process.stderr
            if out or err:
                errors_recalculating.append((subject_id, out, err))

            if verbose:
                print(f"\nRelocking {subject_id}...")
            lock_command = (
                ["python"]
                + locking_data_base_command
                + ["-f"]
                + [form]
                + ["-s"]
                + [subject_id]
                + ["--lock"]
            )
            completed_lock_process = utils.run_command(lock_command, verbose)
            out = completed_lock_process.stdout
            err = completed_lock_process.stderr
            if out or err:
                errors_relocking.append((subject_id, out, err))

        if errors_recalculating or errors_relocking:
            print("\n\nRecalculating errors:\n")
            for error in errors_recalculating:
                print(f"{error[0]}:\nstdout:{error[1]}\nstderr:\n{error[2]}")
            print("\n\nRelocking errors:\n")
            for error in errors_relocking:
                print(f"{error[0]}:\nstdout:{error[1]}\nstderr:\n{error[2]}")

            utils.prompt_close_or_comment(
                issue,
                "Summary scores recalculated, batch_resolve_redcap_update_summary_scores closing now.",
            )
        else:
            utils.close_and_comment(
                issue,
                "Summary scores recalculated, batch_resolve_redcap_update_summary_scores closing now.",
            )
            print(f"No errors recalculating or relocking form. Closed #{issue.number}")


def main():
    """
    Scrapes subject id's from all redcap_update_summary_scores "Failed to import into redcap"-labeled
    issues. Unlocks all clinical forms for each subject id, recalculates the summary scores, and
    relocks them. Retests them and closes the corresponding issue if nothing printed to stdout.
    Otherwise comments on the issue with the contents of stdout.
    """
    args = _parse_args()
    session = _initialize(args)

    session.api.update({"data_entry": None})
    redcap_api = None
    try:
        redcap_api = session.connect_server("data_entry")
    except Exception as e:
        print(e.message)

    metadata = redcap_api.export_metadata(format="df").reset_index()[
        ["form_name", "field_name"]
    ]

    clinical_instruments = metadata['field_name'].str.split('_complete').str[0]
    metadata['instrument'] = np.where(metadata['form_name'] == 'clinical', clinical_instruments, metadata['form_name'])

    forms = list(metadata["form_name"].unique())
    complete_fields = pd.DataFrame(
        {"field_name": [f"{form}_complete" for form in forms], "form_name": forms, "instrument": forms}
    )

    metadata = metadata.append(complete_fields)

    config = _get_config(session)
    run_batch(args.verbose, metadata)


def _parse_args(input_args: Sequence[str] = None) -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser(
        prog="batch_test_import_mr_sessions",
        description="""Scrapes subject id's from all import_mr_sessions-labeled issues. 
        Retests them and closes the corresponding issue if nothing printed to stdout.
        Otherwise comments on the issue with the contents of stdout""",
    )
    sibispy.cli.add_standard_params(parser)
    return parser.parse_args(input_args)


def _initialize(args: argparse.Namespace) -> sibispy.Session:
    """
    Initialize sibispy.Session and start the logger
    """
    slog.init_log(
        verbose=args.verbose,
        post_to_github=True,
        github_issue_title="import_mr_sessions batch run",
        github_issue_label="bug",
        timerDir=None,
    )

    session = sibispy.Session()
    if not session.configure():
        raise RuntimeError("sibispy is not configured; aborting!")
        sys.exit(1)

    return session


def _get_config(session):
    """
    Get the handle for sibis_sys_config.yml.
    """

    parser, error = session.get_config_sys_parser()  # from here, .get_category
    return parser


if __name__ == "__main__":
    main()

