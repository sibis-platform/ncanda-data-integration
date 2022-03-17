#!/usr/bin/env python
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
##
## Scrapes id's from all issues of the passed label. Retests them and closes the
##  corresponding issue if nothing printed to stdout. Otherwise comments on the
##  issue with the contents of stdout.
##
## Example usage: python batch_test_issues.py --labels check_phantom_scans -v
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


def run_batch(label, issue_numbers, metadata, verbose):
    issue_class = utils.get_class_for_label(label)
    title_string = ""

    scraped_issues = utils.scrape_matching_issues(
        slog, metadata, verbose, title_string, label, issue_numbers, issue_class
    )

    if not utils.verify_scraped_issues(scraped_issues):
        print("Aborting this label...")
        return

    utils.update_issues(scraped_issues, verbose)


def main():
    """
    Scrapes id's from all issues of the passed label. Retests them and closes the
    corresponding issue if nothing printed to stdout. Otherwise comments on the
    issue with the contents of stdout.
    """
    args = _parse_args()
    session = _initialize(args)
    config = _get_config(session)

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

    for label in args.labels:
        print(label)
        run_batch(label, args.issue_numbers, metadata, args.verbose)


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
        help="Which labels to scrape issues for (options: import_mr_sessions, check_new_sessions, update_visit_data, check_phantom_scans). Separated by spaces.",
        nargs="+",
        action="store",
        default=None,
    )
    parser.add_argument(
        "--issue_numbers",
        help="Which issue numbers to scrape issues for. Separated by spaces.",
        nargs="+",
        type=int,
        action="store",
        default=[],
    )
    parser.add_argument(
        "-v", "--verbose", help="Verbose operation", action="store_true", default=False
    )

    return parser.parse_args(input_args)


def _initialize(args: argparse.Namespace) -> sibispy.Session:
    """
    Initialize sibispy.Session and start the logger
    """
    slog.init_log(
        verbose=args.verbose,
        post_to_github=True,
        github_issue_title="batch_test_issues",
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
