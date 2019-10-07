#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logic:

1. Retrieve all visit dates + fields indicative of completion for every form
2. Check that visit dates are monotonically increasing and appropriately spaced
3. Check that records without visit dates don't have any data
4. Check that records *with* a visit date *do* have some data
5. Check that records with a visit date don't have data that significantly
    predates or postdates it
"""

# FIXME: Sort the events correctly inside Multiindex
# FIXME: Enforce one arm at a time
# TODO: Each error row creates an issue?
# TODO: Load data locally
# TODO: Move "check" functions into a separate file / module and test discovery
import sibispy
import argparse
import pandas as pd
import redcap as rc
import numpy as np
import sys
import os
from sibispy import sibislogger as slog
import pdb
from load_utils import load_all_forms, chunked_export
from qa_utils import (get_items_matching_regex,
                      get_notnull_entries,
                      count_notnull_entries)
pd.set_option('display.width', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', False)

def main(args):
    if True:
        # FIXME: This file contains duplicates
        df = pd.read_csv(
            '/fs/ncanda-share/beta/simon/full_entry_db.csv',
            low_memory=False,
            index_col=['study_id', 'redcap_event_name'],
            # nrows=300,
        )
    else:
        slog.init_log(args.verbose, args.post_to_github)
        session = sibispy.Session()
        if not session.configure():
            if args.verbose:
                print "Error: session configure file was not found"
            sys.exit()

        api = session.connect_server('data_entry', True)

        if not api:
            if args.verbose:
                print "Error: Could not connect to Redcap"
            sys.exit()

        df = load_all_forms(api)

    # The full data frame is too large to flip through, but we don't really
    # need the values -- we just need count of non-null ones
    visits_and_counts = df.loc[:, ['visit_date', 'visit_ignore___yes']]
    visits_and_counts['notnull_count'] = (df.drop('visit_date', axis=1)
                                          .apply(count_notnull_entries,
                                                 axis=1))
    # TODO: Should automatically collect it?
    # Question: how to determine the kind of input that's expected? automagic
    # pytest-fixture-like mechanism where I look at the name of the argument,
    # check if it corresponds to the name of a preprocessing function, and - if
    # yes - run it?
    checks = [check_visit_date_spacing,
              check_data_with_visit,
              check_no_data_without_visit]
    results = {}
    for check in checks:
        results[check.__name__] = check(visits_and_counts)
        if not results[check.__name__].empty:
            print check.__doc__
            print results[check.__name__]
    all_errors = pd.concat(results.values(), axis=0)
    return all_errors

# Rules for function returns:
# 1. Preserves index - i.e. each index in the returned errorDataFrame will
#    select the corresponding problematic index from the original DataFrame
# 2. Contains all useful information for posting to an issue tracker
#
# It makes most sense to:
#
# 1. Collect each "check" function
# 2. Run it and save its return
# 3. Process it, either by posting to Github or to stdout

def check_visit_date_spacing(df, min_after=120):
    """
    Visits should be spaced at least 120 days apart.
    """
    visits = df.loc[df['visit_date'].notnull(), ['visit_date']]
    visits['next_event'] = visits.index.get_level_values('redcap_event_name')
    visits['next_event'] = visits.groupby(level=0)['next_event'].shift(-1)
    visits.loc[:, 'visit_date'] = pd.to_datetime(visits.loc[:, 'visit_date'])
    visits['next_visit'] = visits.groupby(level=0)['visit_date'].shift(-1)
    visits['gap'] = visits['next_visit'] - visits['visit_date']
    return visits[visits['gap'].dt.days < min_after]


def check_no_data_without_visit(df):
    """
    If visit date is not set, then there should be no data.
    """
    return df[(df['visit_ignore___yes'] != 1) &
              df['visit_date'].isnull() &
              (df['notnull_count'] > 0)]


def check_data_with_visit(df, min_datapoints=5):
    """
    If visit date is set, then there should be some data.
    """
    return df[df['visit_date'].notnull() &
              (df['notnull_count'] <= min_datapoints)]


def check_visit_date_vs_data_dates(df, date_columns, max_before=30, max_after=120):
    # Question: which dates to look at?
    # 1. date fields
    # 2. Record IDs for LimeSurvey imports - will have to be pre-processed
    # - maybe can we make the assumption that all columns
    raise NotImplementedError


if __name__ == '__main__':
    # setup the argument parser and help text
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Verbose operation",
                        action="store_true")
    parser.add_argument("-p", "--post-to-github",
                        help="Post all issues to GitHub instead of stdout.",
                        action="store_true")
    parser.add_argument("-e", "--events", type=int,
                        help="Last event year you want to analyze")
    parser.add_argument("--arm", type=int, default=1,
                        help="Event arms to include")
    parser.add_argument("--include-midyear",
                        help="Include mid-year visits?", 
                        default=False,
                        action="store_true")
    parser.add_argument("--debug",
                        help="Only load subjects for debugging", 
                        default=False,
                        action="store_true")
    parser.add_argument('files', nargs='+')
    # parser.add_argument("-l", "--local-folder",
    #                     help="Folder with release CSVs. (Not implemented.)")
    args = parser.parse_args()
    main(args)
