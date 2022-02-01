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

import batch_script_utils as utils

def run_batch(verbose):
    script_path = "/sibis-software/python-packages/sibispy/cmds/"
    events = ["Baseline", "1y", "2y", "3y", "4y", "5y", "6y"]
    update_scores_base_command = [script_path+"redcap_update_summary_scores.py", "-a", "-s"]
    locking_data_base_command = [script_path+"exec_redcap_locking_data.py", "-e"] + events + ["-f", "Clinical", "-s"]

    title_string = 'redcap_import_record:Failed to import into REDCap'
    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    scraped_tuples = []
    for issue in issues[:200]:
        if title_string in issue.title:
            for label in issue.get_labels():
                if 'redcap_update_summary_scores' == label.name:
                    request_error = utils.rehydrate_issue_body(issue.body)['requestError']
                    subject_ids = utils.extract_unique_subject_ids(request_error)
                    scraped_tuples.append((subject_ids, issue))
                    if verbose:
                        print(f"\nFound the following subject id's in #{issue.number}:\n{subject_ids}")
                    break

    print(f"\nFound the following subject id's:\n{', '.join([', '.join(subject_ids) for subject_ids,_ in scraped_tuples])}")
    if not utils.prompt_y_n("Are all subject id's valid? (y/n)"):
        print("Aborting")
        return

    for subject_ids, issue in scraped_tuples[:1]:
        if verbose:
            print(f"\nResolving issue #{issue.number} with the following id's:\n{subject_ids}\n")

        #Loop through subject id's mentioned in issue since redcap_update_summary_scores.py only recalculates one at a time
        for subject_id in subject_ids[:1]:
            if verbose:
                print(f"Unlocking {subject_id}...")
            unlock_command = ['python'] + locking_data_base_command + [subject_id] + ["--unlock"]
            completed_unlock_process = utils.run_command(unlock_command, verbose)

            if verbose:
                print(f"Recalculating {subject_id}...")
            recalculate_command = ['python'] + update_scores_base_command + [subject_id]
            completed_recalculate_process = utils.run_command(recalculate_command, verbose)

            if verbose:
                print(f"ReLocking {subject_id}...")
            lock_command = ['python'] + locking_data_base_command + [subject_id] + ["--lock"]
            completed_lock_process = utils.run_command(lock_command, verbose)

        utils.prompt_close_or_comment(issue, "Summary scores recalculated, batch_resolve_redcap_update_summary_scores closing now.")


def main():
    """
    Scrapes subject id's from all redcap_update_summary_scores "Failed to import into redcap"-labeled issues. Unlocks all clinical forms for each subject id, recalculates the summary scores, and relocks them. Retests them and closes the corresponding issue if nothing printed to stdout. Otherwise comments on the issue with the contents of stdout.
    """
    args = _parse_args()
    session = _initialize(args)

    session.api.update({'data_entry': None})
    try:
        redcap_api = session.connect_server('data_entry')
    except Exception as e:
        print(e.message)
    field_to_form_map = defaultdict(list)
    for field in redcap_api.export_metadata():
        field_name = field['field_name']
        form_name = field['form_name']
        field_to_form_map[field_name].append(form_name)

    config = _get_config(session)
    run_batch(args.verbose)

def _parse_args(input_args: Sequence[str] = None) -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser(
        prog="batch_test_import_mr_sessions",
        description="Scrapes subject id's from all import_mr_sessions-labeled issues. Retests them and closes the corresponding issue if nothing printed to stdout. Otherwise comments on the issue with the contents of stdout"
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


if __name__ == '__main__':
    main()
