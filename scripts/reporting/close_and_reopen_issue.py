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


def main():
    """
    Closes and reopens github issues with "site_forward" fields and without "waiting_for_site" labels
    """
    args = _parse_args()
    session = _initialize(args)
    config = _get_config(session)
    special_cases = _get_special_cases(session)

    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    for issue in issues:
        if 'site_forward' in issue.body:
            waiting_for_site = False
            for label in issue.get_labels():
                if 'waiting_for_site' == label.name:
                    waiting_for_site = True
            if not waiting_for_site:
                issue.edit(state="closed")
                issue.edit(state="open")




def _parse_args(input_args: Sequence[str] = None) -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser(
        prog="restart_issue",
        description="Closes and reopens github issues with \"site_forward\" fields and without \"waiting_for_site\" labels",
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
        github_issue_title="closed_and_reopened",
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


def _get_special_cases(session) -> Union[Sequence, Mapping]:
    """
    Get the section of the special_cases.yml specific to this script.
    """
    operations_dir = session.get_operations_dir()
    special_cases_file = Path(operations_dir) / 'special_cases.yml'
    if not special_cases_file.exists():
        return

    with open(special_cases_file, 'r') as f:
        all_cases = yaml.safe_load(f)
        file_cases = all_cases.get("restart_issue", {})

    return file_cases


if __name__ == '__main__':
    main()
