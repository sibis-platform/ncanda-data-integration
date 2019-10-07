#!/usr/bin/env python
"""
Given an API, load all the forms, count up their non-NA values, and mark their missing/complete status.
"""

import argparse 
import pandas as pd
import sys
from load_utils import load_form_with_primary_key
from qa_utils import chunked_form_export, get_items_matching_regex
# TODO: chunked_export with configurable key to include on every form (think visit_ignore___yes)
import sibispy
from sibispy import sibislogger as slog

def parse_args(input_args=None):
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
    #parser.add_argument("-x", "--exclude-forms",
    #                    nargs='*')
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


def make_redcap_inventory(api, forms, events=None, post_to_github=False, verbose=False):
    # Determine scope
    meta = api.export_metadata(format='df')
    all_forms = meta['form_name'].unique().tolist()
    if forms is not None:
        all_forms = [form for form in all_forms if form in forms]
    #if exclude_forms is not None:
    #    all_forms = [form for form in all_forms if form not in exclude_forms]
    
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
    
    return pd.concat(final_dfs)

# Apply to DF to get all empty records
def get_flag_and_meta(row):
    try:
        columns = row.columns.tolist()
    except:
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

    slog.init_log(None, None, 
                  'QC: Save the content stats for all forms', 
                  'check_unuploaded_files', None)
    
    # Setting specific constants for this run of QC
    api = session.connect_server(args.api, True)

    # Setting specific constants for this run of QC
    try:
        if args.all_forms:
            forms = None
        else:
            forms = args.forms
        inventory = make_redcap_inventory(api, forms, args.events,
                                          args.post_to_github, verbose=args.verbose)
        inventory.to_csv(args.output, float_format="%.0f")
        sys.exit(0)
    except Exception as e:
        if args.verbose:
            print(sys.exc_info()[0])
        sys.exit(1)
