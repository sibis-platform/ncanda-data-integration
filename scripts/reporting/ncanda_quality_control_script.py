#!/usr/bin/env python
##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##
"""
ncanda_quality_control_script
======================
This script checks the quality of the data for the NCANDA Project on REDCap.
"""
import os
import sys
import json
import datetime

import redcap
import math
import pandas as pd

fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'visit_date','youthreport1_missing','youthreport1_date',
          'youthreport1b_missing', 'youthreport1b_date','youthreport2_missing',
          'youthreport2_date','parentreport_missing','parentreport_date',
          'ssage_youth_missing','ssage_youth_date', 'lssaga1_youth_missing',
          'lssaga1_youth_date','lssaga1_parent_missing','lssaga1_parent_date',
          'mrireport_missing','mrireport_date','mr_session_report_complete'];

def get_project_entry(args=None):
    """
    Pulls the data from REDCap
    """
    # Get API key.
    summary_key_file = open(os.path.join(os.path.expanduser("~"),
                                         '.server_config',
                                         'redcap-dataentry-token'), 'r')
    summary_api_key = summary_key_file.read().strip()

    # Connect to API.
    project_entry = redcap.Project('https://ncanda.sri.com/redcap/api/',
                                   summary_api_key, verify_ssl=False)
    return project_entry

def data_entry_fields(fields,project,arm):
    """
    Gets the dataframe containing a specific arm from REDCap
    """
    # Get a dataframe of fields
    data_entry_raw = project.export_records(fields=fields, format='df',
        events=[arm])
    return data_entry_raw

def exclude_visit_ignore_check(idx,row):
    #exclude with a value of 1 is excluded
    if math.isnan(row.get('exclude')):
        # visit_ignore____yes with value 1 is ignored
        if row.get('visit_ignore___yes') != 1:
            return (idx, row)

def missing_form(idx,row,field_missing, field_value):
    """
    Generate a report indicating which Questionnaires and Forms have not been
    entered
    """
    error = dict()
    idx, row = exclude_visit_ignore_check(idx,row)
    # form is not missing if form_missing if value nan or zero
    if row.get(field_missing) != 1:
        # for form_date, date is stored as a string
        if type(row.get(field_value)) == float:
            error = dict(subject_site_id = idx[0],
                        visit_date = row.get('visit_date'),
                        form_missing = field_missing,
                        event_name = idx[1],
                        visit_notes = row.get('visit_notes'),
                        error = 'ERROR: Form is missing')
    return error

def fourteen_days_MRI_report(idx,row):
    """
    Generate a report indicating which MRI reports have no data after 14 days.
    """
    error = dict()
    idx, row = exclude_visit_ignore_check(idx,row)
        if row.get('mrireport_missing') != 1:
            if type(row.get('mrireport_missing')) == str:
                if datetime.datetime.strptime(row.get('mrireport_date'),'%Y-%m-%d') == datetime.date.today()-datetime.timedelta(days = 14):
                    error = dict(subject_site_id = idx[0],
                                visit_date = row.get('visit_date'),
                                event_name = idx[1],
                                error = 'ERROR: No MRI data after 14 days'
                                )
    return error

def main(args=None):
    project_entry = get_project_entry()
    project_df = data_entry_fields(fields,project_entry,'1y_visit_arm_1')
    error = []

    for idx, row in project_df.iterrows():
        check = missing_form(idx,row)
        if check:
            error.append(check)

    for e in error:
        if e != 'null':
            print json.dumps(e, sort_keys = True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    argv = parser.parse_args()
    sys.exit(main(args=argv))
