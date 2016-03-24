#!/usr/bin/env python
##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
####  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##
"""
youth_report_sex
======================
This script checks whether or not sex was entered correctly in the Youth Report
"""

import os
import sys
import json

import redcap
import math 
import pandas as pd

# Fields
fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'sex', 'youthreport1_missing','youthreport2_missing', 
          'youthreport2_yid2', 'youthreport1_yid2'];

fields_sex = [['youthreport1_missing','youthreport1_yid2'],
			['youthreport2_missing','youthreport2_yid2']]

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

def value_check(idx,row, field_missing, field_sex):
	"""
	Checks to see if dob and cnp_test_sessions_dob match
	"""
	# visit_ignore____yes with value 0 is not ignored
	error = dict()
	if math.isnan(row.get('exclude')):
		if row.get('visit_ignore___yes') != 1:
			# np is not missing if field_missing if value nan or zero
			if row.get(field_missing) != 1:
				if row.get('sex') == row.get(field_sex):
					error = dict(subject_site_id = idx[0],
								visit_date = row.get('visit_date'),
								event_name = idx[1],
								field = field_sex,
								error = 'ERROR: SEX and SEX in YOUTHREPORT do not match.'
								)
	return error

def main(args=None):
	project_entry = get_project_entry()
	project_df = data_entry_fields(fields,project_entry,'1y_visit_arm_1')
	error = []

	# Try using `for` loops rather than `while` to be `pythonic`... this looks like java or c =)
	for idx, row in project_df.iterrows():
		for f in fields_sex:
			check = value_check(idx,row,f[0],f[1])
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
