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


def run_batch(verbose, label):
    if verbose:
        print(f"Searching for {label}...")
    base_command = utils.get_base_command(label)
    id_type = utils.get_id_type(label)

    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    scraped_tuples = []
    for issue in issues:
        for issue_label in issue.get_labels():
            if issue_label.name == label:
                rehydrated_dict = utils.rehydrate_issue_body(issue.body)
                scraped_id = utils.get_id(id_type, rehydrated_dict)
                if scraped_id:
                    if verbose:
                        print(f"Found {scraped_id} in issue #{issue.number}")
                    scraped_tuples.append((scraped_id, issue))
                break

    all_ids = '\n'.join([x for x,y in scraped_tuples])
    print(f"\nFound the following {id_type}s:\n{all_ids}")
    if not utils.prompt_y_n(
        f"Are {id_type}'s valid? Command will run with these. (y/n)"
    ):
        print("Aborting\n")
        return

    closed_issues = []
    commented_issues = []
    for scraped_id, issue in scraped_tuples:
        if verbose:
            print(f"\nTesting issue #{issue.number}, {id_type} {scraped_id}")
        command = ["python"] + base_command + [scraped_id]
        completed_process = utils.run_command(command, verbose)
        if completed_process.stdout or completed_process.stderr:
            if verbose:
                print("Error still produced, commenting on issue")
            issue.create_comment(
                f"Error still produced when {__file__} runs script:\nstdout:\n{completed_process.stdout}stderr:\n{completed_process.stderr}"
            )
            commented_issues.append(f"#{issue.number}")
        else:
            if verbose:
                print("Error no longer produced, closing issue")
            issue.create_comment(f"Error no longer produced, {__file__} closing now.")
            issue.edit(state="closed")
            closed_issues.append(f"#{issue.number}")

    if verbose:
        print(f"\n\nClosed:\n{', '.join(closed_issues)}")
        print(f"Commented:\n{', '.join(commented_issues)}")


def main():
    """
    Scrapes id's from all issues of the passed label. Retests them and closes the
    corresponding issue if nothing printed to stdout. Otherwise comments on the
    issue with the contents of stdout.
    """
    args = _parse_args()
    session = _initialize(args)
    config = _get_config(session)

    for label in args.labels:
        run_batch(args.verbose, label)


def _parse_args(input_args: Sequence[str] = None) -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser(
        prog="batch_test_import_mr_sessions",
        description="""Scrapes id's from all issues of the passed label. Retests 
        them and closes the corresponding issue if nothing printed to stdout. 
        Otherwise comments on the issue with the contents of stdout""",
    )
    parser.add_argument(
        "--labels",
        help="Which labels to scrape issues for (options: import_mr_sessions, check_new_sessions, update_visit_data). Separated by spaces.",
        nargs="+",
        action="store",
        default=None,
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