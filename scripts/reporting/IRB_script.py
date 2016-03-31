#!/usr/bin/env python

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
"""
Reprot: IRB_script
======================
This script generates a report of the numbers needed for the IRB renewal.
"""
import os
import sys
import csv

import redcap
import pandas as pd
import shutil

fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'visit_date'];

forms=['visit_date', 'demographics']

csv_dir="/fs/u00/alfonso/Desktop"
csv_file="{}/bart_list.csv".format(csv_dir)

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

def data_entry_fields(fields,project):
	"""
	Gets the dataframe containing a specific arm from REDCap
	"""
	# Get a dataframe of fields
	data_entry_raw = project.export_records(fields=fields, forms = forms, format='df', events=['baseline_visit_arm_1','1y_visit_arm_1'])
	return data_entry_raw

def number_of_records(df):
    return len(df[df.get('excluded')!= 1])

def main(args):
    project_entry = get_project_entry()
    project_df = data_entry_fields(fields,project_entry)

    project_df.to_csv('/fs/u00/alfonso/project_df.csv')



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    argv = parser.parse_args()
    sys.exit(main(args=argv))
