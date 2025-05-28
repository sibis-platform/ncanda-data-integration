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
    parser.add_argument('-d', '--include-dag',
                        help="Include Redcap Data Access Group for each row",
                        dest="include_dag",
                        action="store_true")
    args = parser.parse_args(input_args)
    return args


def make_redcap_inventory(api: rc.Project,
                          forms: List,
                          events: List = None,
                          post_to_github: bool = False,
                          include_dag: bool = False,
                          verbose: bool = False) -> pd.DataFrame:
    # Determine scope
    meta = api.export_metadata(format_type='df')
    all_forms = meta['form_name'].unique().tolist()
    if forms is not None:
        all_forms = [form for form in all_forms if form in forms]
    
    # always load visit_ignore___yes - if whole visit is ignored, then this
    # form should be, too (very NCANDA-specific)
    data = {form: chunked_form_export(api, forms=[form], events=events,
                                      include_dag=include_dag,
                                      fields=['visit_ignore'])
            for form in all_forms}

    final_dfs = []
    for form in all_forms:
        try:
            form_stats = data[form].apply(get_flag_and_meta, axis=1)
        except ValueError:
            continue
        form_stats['form_name'] = form
        form_stats['status'] = make_classification(form_stats)
        final_dfs.append(form_stats)

    return pd.concat(final_dfs, sort=False)


# Apply to DF to get all empty records
def get_flag_and_meta(row: pd.Series, verbose: bool = True) -> pd.Series:
    try:
        columns = row.columns.tolist()
    except Exception as e:
        # No columns in a Series
        columns = row.index.tolist()

    cols_dag = get_items_matching_regex('redcap_data_access_group', columns)
    cols_complete = get_items_matching_regex(
        "_complete$|^np_reyo_qc___completed$", columns)
    # np_gpeg_exclusion isn't exactly right - it's like a partial missingness
    # reason?
    cols_ignore = get_items_matching_regex(
        "^visit_ignore___yes$|_exclude$|^np_gpeg_exclusion", columns)
    cols_missing = get_items_matching_regex(
        # "^np_reyo_qc___completed$|^bio_mr_same_as_np_day___yes$|_missing$",
        "^bio_mr_same_as_np___yes$|_missing$", columns)
    cols_missing_explanation = get_items_matching_regex(
        "_missing_why(_other)?$", columns)
    cols_checklists = get_items_matching_regex('___', columns)

    # Only keep "normal" checklists that aren't a part of any other things
    cols_checklists_pure = (set(cols_checklists)
                            - set(cols_ignore)
                            - set(cols_complete)
                            - set(cols_missing))
    # after a set operation, preserve order:
    cols_checklists_pure = [c for c in cols_checklists
                            if c in cols_checklists_pure]

    all_meta_cols = (cols_complete + cols_ignore + cols_missing + cols_dag
                     + cols_missing_explanation + cols_checklists)

    result = {}
    if len(cols_dag) > 0:
        result.update({'dag': row['redcap_data_access_group']})

    non_nan_count = row.drop(all_meta_cols).notnull().sum()
    result.update({'non_nan_count': non_nan_count})

    # Count checklists properly
    if cols_checklists_pure:
        col_val1_count = (row[cols_checklists_pure].isin([1, '1'])).sum()
        result.update({'non_nan_count': non_nan_count + col_val1_count})

    # There *can* be multiple sort-of exclusion/missingness columns (for one,
    # we're including visit_ignore___yes on all forms, and some have their own
    # `exclude` switches) - so we'll just assume that wherever there's at least
    # one 1 flipped for exclusion, the form is excluded. Same with missingness.
    #
    # Taking the max of multiple columns is just a quick way to do that.
    if cols_ignore:
        result.update({'exclude': row[cols_ignore].max(skipna=True)})
    if cols_missing:
        result.update({'missing': row[cols_missing].max(skipna=True)})
    if len(cols_complete) > 0:
        if 'np_reyo_qc___completed' in cols_complete:
            # special case: for Reyo QC, the checklist is a completion status,
            # so we should consider it, but the form should also be marked
            # Complete
            result.update({'complete': row[cols_complete].max(skipna=True)})
        else:
            # take the last completion status, on the assumption that it's the
            # overall completion (currently not implementing LSSAGA subparts)
            result.update({'complete': row[cols_complete[-1]]})

    return pd.Series(result)


def make_classification(form: pd.DataFrame) -> pd.Series:
    """
    Return an indexed series of content classifications (present, missing,
    excluded, empty)
    """
    output = pd.Series(index=form.index, dtype=object)
    try:
        idx_missing = form['missing'] == 1
        output.loc[idx_missing] = 'MISSING'
    except KeyError:
        pass

    idx_exclude = form['exclude'] == 1
    idx_present = ((form['non_nan_count'] > 0)
                   & (form['exclude'] != 1))
    idx_empty = form['non_nan_count'] == 0
    if 'missing' in form:
        # NOTE: This is failing for cases where Rey-O wasn't
        # done, so Figure Scores are all hidden and couldn't
        # be done either
        idx_empty = idx_empty & (form['missing'] != 1)

    output.loc[idx_exclude] = 'EXCLUDED'
    # output.loc[idx_present & ~idx_missing] = 'PRESENT'
    # overrides MISSING in cases that have content
    output.loc[idx_present] = 'PRESENT'
    output.loc[idx_empty] = 'EMPTY'

    return output


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
        inventory = inventory.loc[~inventory.index.duplicated(keep=False) |
                                  inventory.index.duplicated(keep='first')]
        inventory.to_csv(args.output, float_format="%.0f")
        sys.exit(0)
    except Exception as e:
        print(e)
        if args.verbose:
            print(sys.exc_info()[0])
        sys.exit(1)
