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
Visit Date Missing
======================
Generate a report indicating which Visit Dates are missing.
"""
import os
import sys
import json
import csv

import redcap
import math
import pandas as pd

# Fields
fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore___yes',
          'visit_date']

#Arms
arms = ['']

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
	data_entry_raw = project.export_records(fields=fields, format='df', events=[arm])
	return data_entry_raw

def visit_data_missing(idx,row):
	"""
	Gets the subjects with missing visit dates
	"""
	error = dict()
	if row.get('exclude') == 0:
		if row.get('visit_ignore___yes') == 0:
			if type(row.get('visit_date')) != str:
				error = dict(subject_site_id = idx[0],
					event_name = idx[1],
					error = 'ERROR: Visit date missing.'
					)
	return error

def main(args=None):
	project_entry = get_project_entry();
	project_df =  data_entry_fields(fields,project_entry,'year1_arm_3');
	error = []

	# Try using `for` loops rather than `while` to be `pythonic`... this looks like java or c =)
	for idx, row in project_df.iterrows():
		error.append(visit_data_missing(idx,row))

	for e in error:
		if e == dict:
			print json.dumps(e, sort_keys = True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    argv = parser.parse_args()
    sys.exit(main(args=argv))