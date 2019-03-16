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
from sibispy import sibislogger as slog

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
            nargs='+',
            action="store")
    # TODO: Allow designation by arm, not (just) by event
    # parser.add_argument(
    #         '-r', '--arm',
    #         help="Which arm to consider?",
    #         default=1, type=int)
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
    pass

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
    data_comp['exceeds']  = data_comp['date'] > data_comp['visit_date'] + pd.Timedelta(days=days_duration)
    data_comp['purgable'] = data_comp['precedes'] | data_comp['exceeds']
    return data_comp


def prepare_blanks_for_form(meta, form_name):
    # Fields to overwrite content with.
    #
    # BONUS: Blank out checkboxes
    # BONUS: Omit calc fields
    # Set form_complete = 0
    pass


def purge_form(api, subject, event, form):
    # TODO: import_records with overwrite='overwrite'
    pass


def main(api, args):
    events = args.events
    # TODO: Use get_events and args.arm to derive a list

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

    # TODO: Use the purge logic
    # marks.apply(purge_form, api, ...

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
    if args.output:
        marks.to_csv(args.output)
    else:
        with pd.option_context('display.max_rows', -1):
            print(marks)
