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
Missing MRI Stroop
======================
Generate a report indicating which MRI Stroop have not been entered.
"""
import os
import sys
import json
import csv

import redcap
import math
import pandas as pd

fields = ['study_id', 'redcap_event_name','redcap_data_access_group','exclude',
		 'visit_ignore', 'visit_date','mri_missing', 'mri_xnat_sid', 
		 'mri_stroop_missing','mri_stroop_date'];

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

def value_check(idx,row):
	"""
	Checks to see if a MRI Stroop is missing
	"""
	# visit_ignore____yes with value 0 is not ignored
	error = dict()
	if math.isnan(row.get('exclude')):
		if row.get('visit_ignore___yes') != 1:
			# MRI Report is not missing if form_missing if value nan or zero
			if row.get('mri_missing') != 1:
				if row.get('redcap_data_access_group') == 'SRI' or row.get('redcap_data_access_group') == 'UCSD':
					if row.get('mri_stroop_missing') == 0:
						# for mri_stroop_date, date is stored as a string, if blank, defaults to NaN
						if type(row.get('mri_stroop_date')) == float:
							error = dict(subject_site_id = idx[0],
									xnat_sid = 'mri_xnat_sid',
									visit_date = row.get('visit_date'),
									event_name = idx[1],
									error = 'ERROR: MRI Stroop is missing'
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