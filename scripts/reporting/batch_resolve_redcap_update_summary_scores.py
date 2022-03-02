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
    title_string = "redcap_import_record:Failed to import into REDCap"
    target_label = "redcap_update_summary_scores"

    def scrape_tuple_from_issue(issue):
        issue_dict = utils.rehydrate_issue_body(issue.body)
        request_error = issue_dict['requestError']
        subject_ids = utils.extract_unique_subject_ids(request_error)
        first_field = request_error.split('","')[1]
        field_row = metadata[metadata["field_name"] == first_field]
        form = field_row["form_name"].item()
        instrument = issue_dict['experiment_site_id'].split("-")[0]

        scraped_tuple = (issue, subject_ids, form, instrument)
        if verbose:
            print(
                f"\nFound the following subject id's in #{issue.number}:\n{subject_ids}"
            )
        return scraped_tuple

    def display_scraped_tuple(scraped_tuple):
        (issue, subject_ids, form, instrument) = scraped_tuple
        for subject_id in subject_ids:
            print("\t".join([subject_id, form, instrument]))

    script_path = "/sibis-software/python-packages/sibispy/cmds/"
    events = ["Baseline", "1y", "2y", "3y", "4y", "5y", "6y", "7y"]
    locking_data_base_command = [
        script_path + "exec_redcap_locking_data.py",
        "-e",
    ] + events
    update_scores_base_command = [
        script_path + "redcap_update_summary_scores.py",
        "-a",
        "-s",
    ]

    def resolve_locking_issue(scraped_tuple):
        (issue, subject_ids, form, instrument) = scraped_tuple
        if verbose:
            print("\n"*20 + "Resolving:")
            display_scraped_tuple(scraped_tuple)

        # Loop through subject id's mentioned in issue since redcap_update_summary_scores.py only recalculates one at a time
        errors = []
        for subject_id in subject_ids:
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
                ["python"]
                + update_scores_base_command
                + [subject_id]
                + ["-i"]
                + [instrument]
            )
            completed_recalculate_process = utils.run_command(
                recalculate_command, verbose
            )
            out = completed_recalculate_process.stdout
            err = completed_recalculate_process.stderr
            if out or err:
                errors.append((out, err))

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
                errors.append((out, err))

        return errors



    close_comment = f"Courtesy of {__file__}:\nSummary scores recalculated, closing."
    error_comment = f"Courtesy of {__file__}:\nErrors produced when recalculating or locking:"

    # Run batch
    scraped_tuples = utils.scrape_matching_issues(
        slog, title_string, target_label, scrape_tuple_from_issue
    )

    if not utils.verify_scraped_tuples(scraped_tuples, display_scraped_tuple):
        print("Aborting...")
        return

    utils.update_issues(scraped_tuples, display_scraped_tuple, resolve_locking_issue, close_comment, error_comment, verbose)
    
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
    
    # Add form_complete field for each form
    forms = list(metadata["form_name"].unique())
    complete_fields = pd.DataFrame(
        {
            "field_name": [f"{form}_complete" for form in forms],
            "form_name": forms,
        }
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
