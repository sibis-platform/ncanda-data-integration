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

import batch_script_utils as utils

def run_batch(args):
    base_command = ["/sibis-software/ncanda-data-integration/scripts/redcap/import_mr_sessions", "-f", "--pipeline-root-dir", "/fs/ncanda-share/cases", "--run-pipeline-script", "/fs/ncanda-share/scripts/bin/ncanda_all_pipelines", "--study-id"]
    
    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    scraped_tuples = []
    for issue in issues:
        if "Missing MRI for Subject" in issue.title:
            for label in issue.get_labels():
                if 'import_mr_sessions' == label.name:
                    subject_id = utils.rehydrate_issue_body(issue.body)['experiment_site_id'][:11]
                    scraped_tuples.append((subject_id, issue))
                    break
                
    print(f"\nFound the following subject ids:\n{[x for x,y in scraped_tuples]}")
    if not utils.prompt_y_n("Are subject id's valid? Command will run with these ids. (y/n)"):
        return

    for subject_id, issue in scraped_tuples:
        if args.verbose:
            print(issue)
            print(f"\nTesting issue #{issue.number}, id {subject_id}")
        command = ['python'] + base_command + [subject_id]
        completed_process = utils.run_command(command, args.verbose)
        if (completed_process.stdout or completed_process.stderr):
            if args.verbose:
                print("Error still produced, commenting on issue")
            issue.create_comment(f"Error still produced by batch_test_import_mr_sessions:\nstdout:\n{complete_process.stdout}\nstderr:\n{completed_process.stderr}")
        else:
            if args.verbose:
                print("Error no longer produced, closing issue")
            issue.create_comment(f"Error no longer produced, batch_test_import_mr_sessions closing now.")
            issue.edit(state="closed")


def main():
    """
    Scrapes subject id's from all import_mr_sessions-labeled issues. Retests them and closes the corresponding issue if nothing printed to stdout. Otherwise comments on the issue with the contents of stdout
    """
    args = _parse_args()
    session = _initialize(args)
    config = _get_config(session)

    run_batch(args)
    
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
