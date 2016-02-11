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
CNP_DOB
======================
This script checks whether or not DOB was entered correctly for WEBCNP
"""

import os
import sys
import json

import redcap
import math 
import pandas as pd

# Fields
fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'dob', 'cnp_test_sessions_dob'];

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
	Gets the dataframe containing data for specific event from REDCap
	"""
	# Get a dataframe of fields
	data_entry_raw = project.export_records(fields=fields, format='df', events=[arm])
	return data_entry_raw

def value_check(idx,row):
	"""
	Checks to see if dob and cnp_test_sessions_dob match
	"""
	# visit_ignore____yes with value 0 is not ignored
	error = dict()
	if math.isnan(row.get('exclude')):
		if row.get('visit_ignore___yes') == 0:
			if row.get('dob') == row.get('cnp_test_sessions_dob'):
				error = dict(subject_site_id = idx[0],
							visit_date = row.get('visit_date'),
							event_name = idx[1],
							error = 'ERROR: DOB and CNP_TEST_SESSIONS_DOB do not match.'
							)
	return error

def main(args=None):
	project_entry = get_project_entry()
	project_df = data_entry_fields(fields,project_entry,'1y_visit_arm_1')
	error = []

	for idx, row in project_df.iterrows():
			check = value_check(idx,row)
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
