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
        request_error = utils.rehydrate_issue_body(issue.body)["requestError"]
        subject_ids = utils.extract_unique_subject_ids(request_error)
        first_field = request_error.split('","')[1]
        field_row = metadata[metadata["field_name"] == first_field]
        form = field_row["form_name"].item()
        instrument = field_row["instrument"].item()

        scraped_tuple = (issue, subject_ids, form, instrument)
        if verbose:
            print(
                f"\nFound the following subject id's in #{issue.number}:\n{subject_ids}"
            )
        return scraped_tuple

    scraped_tuples = utils.scrape_matching_issues(
        slog, title_string, target_label, scrape_tuple_from_issue
    )

    all_found_subject_ids = "\n".join(
        ["\n".join(subject_ids) for _, subject_ids, _, _ in scraped_tuples]
    )
    print(f"\nFound the following subject id's:\n{all_found_subject_ids}")
    if not utils.prompt_y_n("Are all subject id's valid? (y/n)"):
        print("Aborting")
        return

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

    for issue, subject_ids, form, instrument in scraped_tuples:
        print(
            f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nResolving issue #{issue.number} with the following id's:\n{subject_ids}\n"
        )

        # Loop through subject id's mentioned in issue since redcap_update_summary_scores.py only recalculates one at a time
        errors_recalculating = []
        errors_relocking = []
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
                f"Summary scores recalculated, {__file__} closing now.",
            )
        else:
            utils.close_and_comment(
                issue,
                f"Summary scores recalculated, {__file__} closing now.",
            )
            print(f"No errors recalculating or relocking form. Closed #{issue.number}")


def add_instruments_to_metadata(metadata):
    # Get the instrument name for the fields on the clinical form

    # All instrument names without hyphens
    clinical_instruments = metadata["field_name"].str.split("_").str[0]

    # fh_alc, fh_drug
    fh_alc_drug_re = "(fh_alc|fh_drug).*"
    fh_alc_drug_mask = metadata["field_name"].str.contains(fh_alc_drug_re, regex=True)
    fh_alc_drug_instruments = metadata["field_name"].str.extract(fh_alc_drug_re)[0]
    clinical_instruments = np.where(
        fh_alc_drug_mask, fh_alc_drug_instruments, clinical_instruments
    )

    #ssaga_dsm4, ssaga_dsm5
    lssaga_re = "l?(ssaga_dsm(?:4|5)).*"
    lssaga_mask = metadata["field_name"].str.contains(lssaga_re, regex=True)
    lssaga_instruments = metadata["field_name"].str.extract(lssaga_re)[0]
    clinical_instruments = np.where(
        lssaga_mask, lssaga_instruments, clinical_instruments
    )
    
    #cnp_eff
    cnp_re = "cnp.*"
    cnp_mask = metadata["field_name"].str.contains(cnp_re, regex=True)
    cnp_instruments = "cnp_eff"
    clinical_instruments = np.where(
        cnp_mask, cnp_instruments, clinical_instruments
    )

    # Assume the form name is the instrument name, except for fields on the clinical form    
    metadata["instrument"] = np.where(
        metadata["form_name"] == "clinical", clinical_instruments, metadata["form_name"]
    )

    return metadata
            
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
    metadata = add_instruments_to_metadata(metadata)
    
    # Add form_complete field for each form
    forms = list(metadata["form_name"].unique())
    complete_fields = pd.DataFrame(
        {
            "field_name": [f"{form}_complete" for form in forms],
            "form_name": forms,
            "instrument": forms,
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
