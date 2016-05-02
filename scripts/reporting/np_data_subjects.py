#!/usr/bin/env python
##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
"""
np_data_subjects.py
======================
Generate a list of eids for a special subset of subjects. This list can be used
in script/xnat/check_object_names
"""
import os
import sys
import csv

import redcap
import pandas as pd

dir_csv = '/fs/u00/alfonso/Desktop/subset.csv'

template_csv = '/fs/u00/alfonso/Desktop/row.csv'

subject_list = ['B-00017-M-0','B-80403-F-3','E-01008-M-3','E-00966-M-9']

forms=['mr_session_report', 'visit_date','demographics',
'waisiv_arithmetic', 'taylor_complex_figure_scores',
'waisiv_digit_span', 'stroop', 'np_waisiv_coding',
'np_wrat4_word_reading_and_math_computation',
'waisiv_letter_number_sequencing', 'mri_stroop',
'np_reyosterrieth_complex_figure', 'np_landolt_c',
'dkefs_colorword_interference', 'np_grooved_pegboard',
'wasiblock_design', 'cnp_summary',
'paced_auditory_serial_addition_test_pasat',
'np_reyosterrieth_complex_figure_files','np_ishihara',
'np_edinburgh_handedness_inventory', 'biological_np',
'delayed_discounting_100', 'np_modified_greglygraybiel_test_of_ataxia',
'delayed_discounting_1000','youth_report_1','clinical']

visits = ['baseline_visit_arm_1','1y_visit_arm_1']

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

def data_entry_fields(forms,project,arm):
	"""
	Gets the dataframe containing a specific arm from REDCap
	"""
	# Get a dataframe of fields
	data_entry_raw = project.export_records(forms = forms, format='df',
											events=arm)
	return data_entry_raw

def main(args):
    project_entry = get_project_entry()
    project_df = data_entry_fields(forms,project_entry,visits)

    # Filter
    filter_df = project_df.ix[subject_list]
    filter_df.to_csv(dir_csv)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    argv = parser.parse_args()
    sys.exit(main(args=argv))
