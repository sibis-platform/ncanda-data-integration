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


def main():
    """
    Closes and reopens github issues with "site_forward" fields and without "waiting-on-site" labels
    """
    args = _parse_args()
    session = _initialize(args)
    config = _get_config(session)

    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    if args.verbose:
        print("Looping through issues with site_forward in body:")
    for issue in issues:
        if 'site_forward' in issue.body:
            waiting_on_site = False
            for label in issue.get_labels():
                if 'waiting-on-site' == label.name:
                    waiting_on_site = True
            if not waiting_on_site:
                if args.verbose:
                    print(f"\n#{issue.number} missing waiting-on-site label")
                issue.edit(state="closed")
                if args.verbose:
                    print("Closing")
                issue.edit(state="open")
                if args.verbose:
                    print("Reopening")




def _parse_args(input_args: Sequence[str] = None) -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser(
        prog="restart_issue",
        description="Closes and reopens github issues with \"site_forward\" fields and without \"waiting-on-site\" labels",
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



if __name__ == '__main__':
    main()
