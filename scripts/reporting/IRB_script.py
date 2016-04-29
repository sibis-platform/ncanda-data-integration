#!/usr/bin/env python

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
"""
Reprot: IRB_script
======================
This script generates a report of the numbers needed for the IRB renewal.

-y is the year

"""
import os
import sys

import redcap
import pandas as pd
import shutil
import datetime

fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'visit_date'];

forms=['visit_date', 'demographics']

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

def data_entry_fields(fields,project,event):
	"""
	Gets the dataframe containing a specific arm from REDCap
	"""
	# Get a dataframe of fields
	data_entry_raw = project.export_records(fields=fields, forms = forms, format='df', events=event)
	return data_entry_raw

def main(args):
    project_entry = get_project_entry()

    # Calculates the total number of subjects #
    project_df = data_entry_fields(fields,project_entry,['baseline_visit_arm_1'])
    total_number_of_subjects = len(project_df['visit_date'].tolist())

    # Calculates the total number of records #
    project_df = data_entry_fields(fields,project_entry,['baseline_visit_arm_1','1y_visit_arm_1'])
    project_df = project_df[project_df['visit_date'].notnull()]
    total_number_of_records = len(project_df['visit_date'].tolist())

    # Records for the past year #
    year = int(args.yearofirb)
    project_df['visit_date'] = pd.to_datetime(project_df['visit_date'])
    total_number_of_records_this_year = len(project_df[(project_df['visit_date'] > datetime.date((year-1),12,31)) & (project_df['visit_date'] < datetime.date((year+1),1,1)) ]['visit_date'].tolist())

    print "\nIRB Annual Report:"
    print "Total Number of Subjects: {}".format(total_number_of_subjects)
    print "Total Number of Records: {}".format(total_number_of_records)
    print "Total Number of Records the Past Year: {}".format(total_number_of_records_this_year)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--yearofirb', dest="yearofirb",
                        help="The year of the IRB renewal", action='store')
    argv = parser.parse_args()
    sys.exit(main(args=argv))
