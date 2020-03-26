#!/usr/bin/env python
"""
Use inventories made by make_redcap_inventory to run checks if all forms within
a group are present or otherwise accounted for
"""
import argparse
import pandas as pd
import sibispy
from typing import List
from sibispy import cli
import sys
from pathlib import Path
import pdb

FORM_GROUPS = {
    'sleep': [
        'sleep_study_evening_questionnaire',
        'sleep_study_presleep_questionnaire',
        'sleep_study_morning_questionnaire'
    ],
    'mri': [
        'mr_session_report',
        'mri_report'
    ],
    "np": [
        'np_wrat4_word_reading_and_math_computation',
        'np_grooved_pegboard',
        'np_reyosterrieth_complex_figure_files',
        'np_reyosterrieth_complex_figure',
        'np_modified_greglygraybiel_test_of_ataxia',
        'np_waisiv_coding'
    ],
    'deldisc_stroop': [
        'delayed_discounting_1000',
        'delayed_discounting_100',
        'stroop'],
    'deldisc': [
        'delayed_discounting_1000',
        'delayed_discounting_100'
    ],
    'youth_report': [
        'youth_report_1',
        'youth_report_1b',
        'youth_report_2',
    ],
    'youth_report_lssaga': [
        'youth_report_1',
        'youth_report_1b',
        'youth_report_2',
        'limesurvey_ssaga_youth'
    ],
}


def parse_args(input_args: List = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Verbose operation",
                        action="store_true")
    parser.add_argument("-x", "--failures-only",
                        help="Only output problematic cases",
                        action="store_true")
    parser.add_argument('-g', '--group', '--form-group',
                        dest='form_group',
                        help="Form group to evaluate",
                        choices=FORM_GROUPS.keys(),
                        required=True)
    parser.add_argument('-o', '--output',
                        help="CSV file to write the results to",
                        default=sys.stdout)
    parser.add_argument('input_dir',
                        help="Directory that stores the inventory subsets "
                             "required in this operation",
                        type=Path)
    args = parser.parse_args(input_args)
    return args


def process_form_group(forms, inventory_dir, form_group_name: str = 'Check?'):
    # 1. condense each form to "data present?" (marked missing => data present
    #    for purposes of entry completeness checking) and name this column
    #    after the form
    # 2. Set index to id,event,form
    # 3. Join on index, get anyplace where row.any() and not row.all()
    data = {form: (pd.read_csv(inventory_dir / F"{form}.csv"))
            for form in forms}
    for form in forms:
        form_data = data[form]
        idx_missing = form_data['missing'] == 1
        idx_exclude = form_data['exclude'] == 1
        idx_present = (form_data['non_nan_count'] > 0) & (form_data['exclude'] != 1)
        idx_empty = (form_data['non_nan_count'] == 0) & (form_data['missing'] != 1)

        data[form].loc[idx_missing, form] = 'MISSING'
        data[form].loc[idx_exclude, form] = 'EXCLUDED'
        data[form].loc[idx_present, form] = 'PRESENT'
        data[form].loc[idx_empty, form] = 'EMPTY'

        data[form] = (data[form]
                      .set_index(['study_id', 'redcap_event_name'])
                      .loc[:, [form]])
        data[form]
    all_data = pd.concat(data.values(), axis=1, sort=False)
    all_data[form_group_name] = (all_data.apply(
        lambda row: ((row == 'PRESENT').all()
                     or ((row == 'PRESENT').any()
                         and not (row == 'EMPTY').any())
                     or not (row == 'PRESENT').any()),
        axis=1))

    return all_data


if __name__ == '__main__':
    args = parse_args()
    forms_to_process = FORM_GROUPS.get(args.form_group)
    report = process_form_group(forms=forms_to_process,
                                inventory_dir=args.input_dir,
                                form_group_name=args.form_group)
    if args.failures_only:
        failures_only_df = report.loc[~report[args.form_group]]
        if not failures_only_df.empty:
            failures_only_df.to_csv(args.output)
        elif args.verbose:
            print(F"No failures for {args.form_group}!")
    else:
        report.to_csv(args.output)
