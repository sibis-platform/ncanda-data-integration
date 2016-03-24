#!/usr/bin/env python
##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
####  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##
"""
Missing_Saliva_Sample
======================
Generate a report indicating which Saliva Samples have not been entered.
"""
import os
import sys
import json
import csv

import redcap
import math
import pandas as pd

fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'visit_date','saliva_missing','saliva_1_collected','saliva_1_date',
          'saliva_2_collected','saliva_2_date','saliva_3_collected',
          'saliva_3_date','saliva_4_collected','saliva_4_date'];

saliva_fields = [['saliva_1_collected','saliva_1_date'],
          ['saliva_2_collected','saliva_2_date'],['saliva_3_collected',
          'saliva_3_date'],['saliva_4_collected','saliva_4_date']];

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

def value_check(idx,row,saliva_collected, saliva_date):
	"""
	Checks to see if an form is missing
	"""
	# visit_ignore____yes with value 0 is not ignored
	error = dict()
	if math.isnan(row.get('exclude')):
		if row.get('visit_ignore___yes') != 1:
			# saliva_sample is not missing if saliva_sample_missing if value zero
			if row.get('saliva_missing') != 1:
				if row.get(saliva_collected) == 1:
				# for form_date, date is stored as a string
					if type(row.get(saliva_date)) == float:
						error = dict(subject_site_id = idx[0],
								visit_date = row.get('visit_date'),
								event_name = idx[1],
								sample_missing = saliva_collected,
								visit_notes = row.get('visit_notes'),
								error = 'ERROR: Saliva Sample is missing'
								)
	return error

def main(args=None):
	project_entry = get_project_entry()
	project_df = data_entry_fields(fields,project_entry,'1y_visit_arm_1')
	error = []
	
	for idx, row in project_df.iterrows():
		for s in saliva_fields:
			check = value_check(idx,row,s[0],s[1])
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