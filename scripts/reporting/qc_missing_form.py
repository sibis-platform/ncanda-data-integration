#!/usr/bin/env python
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
####  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##
"""
Missing Forms
======================
Generate a report indicating which Questionnaires and Forms have not been entered.
"""
from __future__ import print_function
import os
import sys
import json
import csv

import redcap
import math
import pandas as pd

fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'visit_date','visit_notes','youthreport1_missing','youthreport1_date',
          'youthreport1b_missing', 'youthreport1b_date','youthreport2_missing',
          'youthreport2_date','parentreport_missing','parentreport_date',
          'ssage_youth_missing','ssage_youth_date', 'lssaga1_youth_missing',
          'lssaga1_youth_date','lssaga1_parent_missing','lssaga1_parent_date'];

form_fields = [['youthreport1_missing','youthreport1_date'],
          ['youthreport1b_missing', 'youthreport1b_date'],['youthreport2_missing',
          'youthreport2_date'],['parentreport_missing','parentreport_date'],
          ['ssage_youth_missing','ssage_youth_date'],['lssaga1_youth_missing',
          'lssaga1_youth_date'],['lssaga1_parent_missing','lssaga1_parent_date']];


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

def value_check(idx,row,field_missing, field_value):
	"""
	Checks to see if an form is missing
	"""
	# visit_ignore____yes with value 0 is not ignored
	error = dict()
	if math.isnan(row.get('exclude')):
		if row.get('visit_ignore___yes') != 1:
			# form is not missing if form_missing if value nan or zero
			if row.get(field_missing) != 1:
				# for form_date, date is stored as a string
				if type(row.get(field_value)) == float:
					error = dict(subject_site_id = idx[0],
							visit_date = row.get('visit_date'),
							form_missing = field_missing,
							event_name = idx[1],
							visit_notes = row.get('visit_notes'),
							error = 'ERROR: Form is missing'
							)
	return error

def main(args=None):
	project_entry = get_project_entry()
	project_df = data_entry_fields(fields,project_entry,'1y_visit_arm_1')
	error = []

	for idx, row in project_df.iterrows():
		for f in form_fields:
			check = value_check(idx,row,f[0],f[1])
			if check:
				error.append(check)

	for e in error:
		if e != 'null':
			print(json.dumps(e, sort_keys = True))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    argv = parser.parse_args()
    sys.exit(main(args=argv))
