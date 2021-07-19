#!/usr/bin/env python
"""
1. For arm of choice, retrieve associated date variables via export_fem.
2. Select comparison date variable - by default, visit_date, although other
   arms have other fields?
3. Retrieve the date variables from given arm
4. Apply a mask to determine which variables precede or exceed the comparison
   date variable
5. Raise errors for each variable independently

TODO: Reflect exceptions set in special_cases.yml::outside_visit_window and
::update_visit_data.
"""

import argparse
import os
import pandas as pd
import sys
import sibispy
from six import string_types
from sibispy import sibislogger as slog
import json
import yaml


def parse_args(arg_input=None):
    parser = argparse.ArgumentParser(
        description="Find all Entry forms that precede or exceed a given date")
    parser.add_argument("-v", "--verbose",
                        action="store_true")
    parser.add_argument(
        "--max-days-after-visit",
        help="Assignment of form to event is illegal after N days",
        action="store",
        default=120,
        type=int)
    parser.add_argument(
        "-s", "--subjects",
        help="Limit processing to selected space-separated subjects",
        nargs='*',
        action="store",
        default=None)
    parser.add_argument(
        '-c', '--comparison-date-var',
        help="Date against which the other dates will be compared. Must be on "
        "the designated arm and event. By default, the first eligible variable"
        " in the data dictionary becomes the comparison variable. (The best "
        "comparison variable is visit_date.)",
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
        "-p", "--post-to-github",
        help="Post all issues to GitHub instead of stdout.",
        action="store_true")
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        '-o', '--output',
        help="Path to a writable CSV.",
        default=None)
    output.add_argument(
        '-q', '--no-output',
        help="Don't write out the output DataFrame",
        action="store_true"
    )

    return parser.parse_args(arg_input)


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
    data_comp['precedes'] = data_comp['date'] < data_comp['visit_date']
    data_comp['exceeds'] = data_comp['date'] > (
        data_comp['visit_date'] + pd.Timedelta(days=days_duration))
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

def get_special_cases(marks, session):
    """
    Looks at special_cases.yml file, finds the special cases under the file name section,
    and then excludes any cases that match the special cases list.

    Note (for Chris use):
    - 'redcap_event_name' is arm name
    - 'study_id' inclues up to letter and number
    - 'visit_date' is looking at date --> not correct!

    Each row in the dataframe has:
    row.name -> [0] is the subject ID, [1] is the arm name
    """

    # Connect to the special_cases.yml file
    sibis_config = session.get_operations_dir()
    special_cases_file = os.path.join(sibis_config, 'special_cases.yml')
    if not os.path.isfile(special_cases_file):
        slog.info("wrong_date_associations","Error: The following file does not exist : " + special_cases_file)
        sys.exit(1)

    # Get a list of the specific cases that should be inspected
    with open(special_cases_file) as fi:
        special_cases = yaml.load(fi)
        exceptions_data = special_cases.get('wrong_date_associations', {})

    # Loop through each exception and drop the corresponding row
    for exception in exceptions_data:
        for index, row in marks.iterrows():
            # Find matching subject and drop
            if (exception['subject'] == row.name[0] and exception['event'] == row.name[1] and exception['dates'] == row['form_date_var']):
                marks = marks.drop(index)

    return marks
    
def main(api, args):
    events = []
    arm = args.arm

    # Handling no events arg, so all events are chosen
    # Note: should it always pull from one arm when all forms or all arms?
    if (args.events is None):
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
    args = parse_args()

    slog.init_log(args.verbose, args.post_to_github,
                  'Incorrectly associated date and event',
                  'wrong_date_association', None)

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
    marks = get_special_cases(marks, session)
    
    # Changeable UID template for logging each dataframe by row
    UID_TEMPLATE = "WrongDate-{study_id}/{redcap_event_name}/{form}"
    RESOLUTION = ("Contact site to determine if the date is incorrect and "
                  "should be changed, if the form should be emptied, or if an "
                  "exception should be set.")

    # Log dataframe by row here, one for exceeds, and another for precedes
    log_dataframe_by_row(
        marks[marks['exceeds']],
        uid_template=UID_TEMPLATE,
        message=f"Form exceeds visit date by {args.max_days_after_visit} days",
        resolution=RESOLUTION)
    log_dataframe_by_row(
        marks[marks['precedes']],
        uid_template=UID_TEMPLATE,
        message=f"Form precedes visit date by a non-zero number of days",
        resolution=RESOLUTION)

    if args.output:
        marks.to_csv(args.output)
    elif args.no_output:
        pass
    else:
        with pd.option_context('display.max_rows', None):
            print(marks)
