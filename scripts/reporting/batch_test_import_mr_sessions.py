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
from subprocess import run

def main():
    """
    Scrapes subject id's from all import_mr_sessions-labeled issues. Retests them and closes the corresponding issue if nothing printed to stdout. Otherwise comments on the issue with the contents of stdout
    """
    args = _parse_args()
    session = _initialize(args)
    config = _get_config(session)

    base_command = "/sibis-software/ncanda-data-integration/scripts/redcap/import_mr_sessions -f --pipeline-root-dir /fs/ncanda-share/cases --run-pipeline-script /fs/ncanda-share/scripts/bin/ncanda_all_pipelines --study-id "
    
    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    for issue in issues:
        for label in issue.get_labels():
            if 'import_mr_sessions' == label.name:
                subject_id = issue.body.split('experiment_site_id: ')[1][:11]
                if args.verbose:
                    print(f"\nRetesting issue #{issue.number}, subject id {subject_id}")

                command = base_command + subject_id
                completed_process = run(['python'] + command.split(), capture_output=True)
                if not completed_process.stdout:
                    if args.verbose:
                        print("Error no longer produced, closing issue")
                    issue.create_comment("Error no longer produced, batch_test_import_mr_sessions closing now.")
                    issue.edit(state="closed")
                else:
                    if args.verbose:
                        print("Error still produced, commenting on issue")
                    issue.create_comment("Error still produced by batch_test_import_mr_sessions: \n {complete_process.stdout}.")
                break

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
