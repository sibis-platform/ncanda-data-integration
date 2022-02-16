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
        {"field_name": [f"{form}_complete" for form in forms], "form_name": forms}
    )

    metadata = metadata.append(complete_fields)

    config = _get_config(session)
    print(metadata[metadata['field_name'] == args.field_name]['form_name'].item())


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
    parser.add_argument(
        "field_name",
        help="Field name to find form for.",
        action="store",
        type=str,
        default=None,
    )
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
