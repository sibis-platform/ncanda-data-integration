#!/usr/bin/env python
"""
Given an API, load all the forms, count up their non-NA values, and mark their missing/complete status.
"""

import argparse
import pandas as pd
import pdb
import redcap as rc
import sys
from load_utils import load_form_with_primary_key
from qa_utils import chunked_form_export, get_items_matching_regex
# TODO: chunked_export with configurable key to include on every form (think visit_ignore___yes)
import sibispy
from sibispy import sibislogger as slog
from typing import List


def parse_args(input_args: List = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Verbose operation",
                        action="store_true")
    parser.add_argument("-p", "--post-to-github",
                        help="Post all issues to GitHub instead of stdout.",
                        action="store_true")
    parser.add_argument("-a", "--all-forms",
                        action='store_true')
    parser.add_argument("-f", "--forms",
                        nargs='+')
    parser.add_argument("-e", "--events",
                        nargs='*')
    parser.add_argument('-o', '--output',
                        help="File to save the inventory to",
                        default=sys.stdout)
    parser.add_argument('-s', '--api',
                        help="Source Redcap API to use",
                        default="data_entry")
    args = parser.parse_args(input_args)
    return args


def make_redcap_inventory(api: rc.Project,
                          forms: List,
                          events: List = None,
                          post_to_github: bool = False,
                          include_dag: bool = False,
                          verbose: bool = False) -> pd.DataFrame:
    # Determine scope
    meta = api.export_metadata(format='df')
    all_forms = meta['form_name'].unique().tolist()
    if forms is not None:
        all_forms = [form for form in all_forms if form in forms]
    
    data = {form: chunked_form_export(api, forms=[form], events=events) for form in all_forms}
    # FIXME: Drop fully empty columns
    final_dfs = []
    for form in all_forms:
        try:
            form_stats = data[form].apply(get_flag_and_meta, axis=1)
        except ValueError:
            continue
        form_stats['form_name'] = form
        final_dfs.append(form_stats)

    return pd.concat(final_dfs, sort=False)


# Apply to DF to get all empty records
def get_flag_and_meta(row: pd.Series, verbose: bool = True) -> pd.Series:
    try:
        columns = row.columns.tolist()
    except Exception as e:
        # No columns in a Series
        columns = row.index.tolist()
    
    cols_complete = get_items_matching_regex("_complete$", columns)
    cols_ignore = get_items_matching_regex("^visit_ignore___yes$|_exclude$", columns)
    cols_missing = get_items_matching_regex("_missing$", columns)
    cols_missing_explanation = get_items_matching_regex("_missing_why(_other)?$", columns)
    cols_checklists = get_items_matching_regex('___', columns)
    
    all_meta_cols = cols_complete + cols_ignore + cols_missing + cols_missing_explanation + cols_checklists
    
    # NOTE: This will only work for a Series
    # NOTE: For a full Data Frame, use df.drop(drop_columns, axis=1).notnull().sum(axis=1)
    non_nan_count = row.drop(all_meta_cols).notnull().sum()
    
    result = {'non_nan_count': non_nan_count}
    # always take last completeness status, on the assumption that that's the true one
    # (currently not implementing LSSAGA subparts)
    if len(cols_complete) > 0:
        result.update({'complete': row[cols_complete[-1]]})
    if cols_ignore:
        result.update({'exclude': row[cols_ignore[0]]})
    if cols_missing:
        result.update({'missing': row[cols_missing[0]]})
    
    return pd.Series(result)


if __name__ == '__main__':
    args = parse_args()
    session = sibispy.Session()
    if not session.configure():
        sys.exit()

    slog.init_log(verbose=args.verbose,
                  post_to_github=args.post_to_github,
                  github_issue_title='QC: Save content stats by form',
                  github_issue_label='inventory',
                  timerDir=None)

    # Setting specific constants for this run of QC
    api = session.connect_server(args.api, timeFlag=True)

    try:
        if args.all_forms:
            forms = None
        else:
            forms = args.forms
        inventory = make_redcap_inventory(api=api,
                                          forms=forms,
                                          events=args.events,
                                          post_to_github=args.post_to_github,
                                          include_dag=args.include_dag,
                                          verbose=args.verbose)
        inventory.to_csv(args.output, float_format="%.0f")
        sys.exit(0)
    except Exception as e:
        print(e)
        if args.verbose:
            print(sys.exc_info()[0])
        sys.exit(1)
