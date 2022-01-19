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

def run_batch():
    script_path = Path("/sibis-software/python-packages/sibispy/cmds/")
    events = ["Baseline", "1y", "2y", "3y", "4y", "5y", "6y"]
    updates_scores_base_command = [script_path / "redcap_update_summary_scores", "-a", "-s"]
    locking_data_base_command = [script_path / "exec_redcap_locking_data", "-e"] + events + ["-f", "Clinical", "-s"]

    title_string = 'redcap_import_record:Failed to import into REDCap'
    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    for issue in issues:
        if title_string in issue.title:
            for label in issue.get_labels():
                if 'redcap_update_summary_scores' == label.name:
                    request_error = rehydrate_issue_body(issue.body)['requestError']
                    subject_ids = extract_unique_subject_ids(request_error)

                    print(f"\nFound the following subject id's in #{issue.number}:\n{subject_ids}")
                    if not prompt_y_n("Are all subject id's valid? Command will run with these id's. (y/n)"):
                        return

                    unlock_command = ['python'] + locking_data_base_command + subject_ids + ["--unlock"]
                    completed_unlock_process = run_command(command, args.verbose)

                    recalculate_command = ['python'] + update_scores_base_command + subject_ids
                    completed_recalculate_process = run_command(command, args.verbose)

                    lock_command = ['python'] + locking_data_base_command + subject_ids + ["--lock"]
                    completed_lock_process = run_command(command, args.verbose)

                    prompt_close_or_comment(issue, "Summary scores recalculated, batch_resolve_redcap_update_summary_scores closing now.")
                    break


def main():
    """
    Scrapes subject id's from all redcap_update_summary_scores "Failed to import into redcap"-labeled issues. Unlocks all clinical forms for each subject id, recalculates the summary scores, and relocks them. Retests them and closes the corresponding issue if nothing printed to stdout. Otherwise comments on the issue with the contents of stdout.
    """
    args = _parse_args()
    session = _initialize(args)
    config = _get_config(session)
    run_batch()

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
