#!/usr/bin/env python
"""

1. For arm of choice, retrieve associated date variables via export_fem. ('_date$' will work, except on MRI Session Report - or maybe there, too?)
2. Select comparison date variable - by default, visit_date, although other arms have other fields?
3. Retrieve the date variables from given arm
4. Apply a mask to determine which variables precede the comparison date variable
5. Determine which variables/instruments to purge, based on the mask
    - wrinkle 1: MRI Session Report
    - wrinkle 2: LSSAGA is imported in four parts, so the purge should only affect one
    ...or, anytime a date is off on an instrument, just purge it and let the pipeline reassign as needed?
6. If not dry run, purge them

1. Allow specification by ID, event, arm?, form subset

FUTURE: In addition to outdated, also mark "beyond M days after comparison date"
"""

import argparse
import pandas as pd
import sys
import sibispy
from six import string_types
from sibispy import sibislogger as slog
import json

# Changeable UID template for logging each dataframe by row
UID_TEMPLATE = "Wrong date - {study_id}/{redcap_event_name}/{form}"

def parse_args(arg_input=None):
    parser = argparse.ArgumentParser(
            description="Find and purge all Entry forms that precede the visit date",)
    parser.add_argument("-v", "--verbose",
            action="store_true")
    parser.add_argument(
            "--max-days-after-visit",
            help="Maximum number of days the scan session can be after the entered 'visit date' in REDCap to be assigned to a given event.",
            action="store",
            default=120,
            type=int)
    parser.add_argument(
            "-s", "--subjects",
            help="Limit processing to subject id (e.g., A-00000-F-1)",
            nargs='*',
            action="store",
            default=None)
    parser.add_argument(
            '-c', '--comparison-date-var',
            help="Date against which the other dates will be compared. Must be on "
            "the designated arm and event. By default, the first eligible variable"
            " in the data dictionary becomes the comparison variable",
            default=None)
    parser.add_argument(
            '-e', "--events",
            help="Only process specific event(s)",
            nargs='*',
            action="store")
    parser.add_argument(
            '-r', '--arm',
            help="Which arm to consider?",
            default=1, type=int)
    parser.add_argument(
            "-n", "--dry-run",
            help="Check date validity but don't purge instruments",
            action="store_true")
    parser.add_argument(
            "-p", "--post-to-github",
            help="Post all issues to GitHub instead of std out.",
            action="store_true")
    parser.add_argument(
            '-o', '--output',
            help="Path to a writable CSV with purgable results.",
            default=None)

    return parser.parse_args()
    # return parser.parse_args(arg_input)

def get_events(api, events=None, arm=None):
    # Based on arguments that were passed, output Redcap-compatible event names
    # for further consumption

    event_names = []        
    for event in api.events:
        if (event["unique_event_name"] in events):
            if (event["arm_num"] == arm):
                event_names.append(event["unique_event_name"])
    return event_names

def get_date_vars_for_arm(api, events, datevar_pattern=r'_date$'):
    # Given a list of events, retrieve a list of date variables
    fem = api.export_fem(format='df')
    available_forms = fem[fem['unique_event_name'].isin(events)]['form'].unique()
    meta = api.export_metadata(format='df')
    meta_subset = meta.loc[
            meta['form_name'].isin(available_forms) &
            meta.index.str.contains(datevar_pattern)]
    return meta_subset.index.tolist()
    # return meta_subset['form_name'].to_dict()

def get_form_lookup_for_vars(varnames, metadata):
    return metadata.loc[varnames, 'form_name'].to_dict()

def retrieve_date_data(api, fields, events=None, records=None):
    # output should have pandas.Datetime dtype
    data = api.export_records(fields=fields, events=events, records=records,
                              format='df',
                              df_kwargs={
                                  'index_col': [api.def_field, 'redcap_event_name'],
                                  'dtype': object,
                                  'parse_dates': fields,
                              })
    return data

def mark_lagging_dates(data, comparison_var, days_duration):
    comparisons = data.loc[:, [comparison_var]]
    df = data.drop(columns=[comparison_var]).copy()
    df.columns.name = 'form_date_var'  # so that stacking index has a name
    data_long = df.stack().to_frame('date').reset_index(-1)
    data_comp = data_long.join(comparisons)
    # Maybe extract previous code into data prep?
    print(data_comp)
    data_comp['precedes'] = data_comp['date'] < data_comp['visit_date']
    data_comp['exceeds']  = data_comp['date'] > data_comp['visit_date'] + pd.Timedelta(days=days_duration)
    data_comp['purgable'] = data_comp['precedes'] | data_comp['exceeds']
    return data_comp

def log_dataframe_by_row(errors_df: pd.DataFrame,
                         uid_template: str = "{id}/{redcap_event_name}/{form}",
                         **kwargs):
    """
    Convert each row of the DataFrame into a Sibislogger issue.
    General idea: Each column in errors_df is reported, each additional keyword
    argument is a template that gets populated with data from the columns.

    Note: imported from 'error_handling.py' within 'hivalc-data-integration'
    """

    def log_row(row: pd.Series, **kwargs):
        kwargs.update({
            k: v.format(**row) for k, v in kwargs.items()
            if isinstance(v, string_types)
        })
        slog.info(
            **kwargs,
            **row.dropna())

    for _, row in errors_df.reset_index().iterrows():
        log_row(row, uid=uid_template, **kwargs)

def main(api, args):
    events = []
    arm = args.arm
    print(arm)
    # Handling no events arg, so all events are chosen
    # Note: should it always pull from one arm when all forms or all arms?
    if (args.events == None):
        for event in api.events:
            events.append(event["unique_event_name"])
    else:
        events = args.events

    events = get_events(api, events, arm)
    datevars = get_date_vars_for_arm(api, events)
    if args.comparison_date_var:
        comparison_date_var = args.comparison_date_var
    else:
        comparison_date_var = datevars[0]

    meta = api.export_metadata(format='df')
    lookup = get_form_lookup_for_vars(datevars, meta)
    data = retrieve_date_data(api, fields=datevars, events=events, 
                              records=args.subjects)

    marks = mark_lagging_dates(data, comparison_date_var, 
                               days_duration=args.max_days_after_visit)

    marks['form'] = marks['form_date_var'].map(lookup)

    # Convert 'date' and 'visit_date' to strings to make them JSON serializable
    marks['date'] = marks['date'].astype(str)
    marks['visit_date'] = marks['visit_date'].astype(str)

    return marks[marks['purgable']]


if __name__ == '__main__':
    args = parse_args(sys.argv)

    slog.init_log(args.verbose, args.post_to_github, 'Purge date from Entry',
            'purge_outdated', None)

    slog.startTimer1()

    session = sibispy.Session()
    if not session.configure():
        if args.verbose:
            print("Error: session configure file was not found")
        sys.exit()

    redcap_api = session.connect_server('data_entry', True)
    if not redcap_api:
        if args.verbose:
            print("Error: Could not connect to Redcap")
        sys.exit()

    marks = main(redcap_api, args)

    # Log dataframe by row here, one for exceeds, and another for precedes
    log_dataframe_by_row(marks[marks['exceeds']], uid_template=UID_TEMPLATE, message="Entry form exceeds visit date.",
        description="Listed is an entry form that exceeds the visit date by 120 days.")
    log_dataframe_by_row(marks[marks['precedes']], uid_template=UID_TEMPLATE, message="Entry forms precedes visit date.",
        description="Listed is an entry form that precedes the visit date.")

    if args.output:
        marks.to_csv(args.output)
    else:
        with pd.option_context('display.max_rows', 1):
            print(marks)
