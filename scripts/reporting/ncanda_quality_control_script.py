#!/usr/bin/env python
##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
####  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##
"""
ncanda_quality_control_script
======================
This script checks the quality of the data for the NCANDA Project on REDCap.
Call script on command line.

Example Usage:
python ncanda_quality_control_script.py -a "baseline_visit_arm_1"
"""
import os
import sys
import json
import datetime

import redcap
import math
import pandas as pd

import sibis

fields = ['study_id', 'redcap_event_name','exclude', 'visit_ignore',
          'visit_date', 'dob', 'cnp_test_sessions_dob','saliva_missing',
          'saliva_1_collected','saliva_1_date','saliva_2_collected','saliva_2_date',
          'saliva_3_collected','saliva_3_date','saliva_4_collected',
          'saliva_4_date','youthreport1_missing','youthreport1_date',
          'youthreport1b_missing', 'youthreport1b_date','youthreport2_missing',
          'youthreport2_date','youthreport2_yid2', 'youthreport1_yid2',
          'parentreport_missing','parentreport_date','ssage_youth_missing',
          'ssage_youth_date', 'lssaga1_youth_missing','lssaga1_youth_date',
          'lssaga1_parent_missing','lssaga1_parent_date','bio_np_missing',
          'bio_np_date','dd1000_missing','dd1000_date','dd100_missing',
          'dd100_date','np_wrat4_missing','np_wrat4_wr_raw','np_gpeg_missing',
          'np_gpeg_exclusion','np_gpeg_dh_time','np_gpeg_ndh_time',
          'np_reyo_missing','np_reyo_copy_time','np_reyo_qc(completed)',
          'np_atax_missing','np_atax_sht_trial1','np_wais4_missing',
          'np_wais4_rawscore','np_wais4_rawscore_computed',
          'np_wais4_rawscore_diff(correct)','pasat_missing','pasat_date',
          'cnp_missing','cnp_test_sessions_dotest','stroop_missing',
          'stroop_date','mrireport_missing','mrireport_date',
          'mr_session_report_complete']

form_fields = [['youthreport1_missing','youthreport1_date'],
                ['youthreport1b_missing', 'youthreport1b_date'],
                ['youthreport2_missing', 'youthreport2_date'],
                ['parentreport_missing','parentreport_date'],
                ['ssage_youth_missing','ssage_youth_date'],
                ['lssaga1_youth_missing','lssaga1_youth_date'],
                ['lssaga1_parent_missing','lssaga1_parent_date'],
                ['bio_np_missing', 'bio_np_date'],
                ['dd1000_missing','dd1000_date'],
                ['dd100_missing','dd100_date'],
                ['np_wrat4_missing','np_wrat4_wr_raw'],
                ['np_reyo_missing','np_reyo_copy_time'],
                ['np_atax_missing','np_atax_sht_trial1'],
                ['np_wais4_missing', 'np_wais4_rawscore'],
                ['pasat_missing','pasat_date'],
                ['cnp_missing','cnp_test_sessions_dotest'],
                ['stroop_missing','stroop_date']]

np_gpeg_fields = [['np_gpeg_exclusion___dh','np_gpeg_dh_time'],
                  ['np_gpeg_exclusion___ndh','np_gpeg_ndh_time']]

saliva_fields = [['saliva_1_collected','saliva_1_date'],
          ['saliva_2_collected','saliva_2_date'],['saliva_3_collected',
          'saliva_3_date'],['saliva_4_collected','saliva_4_date']]

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
    Gets the dataframe containing a specific arm from REDCap
    """
    # Get a dataframe of fields
    data_entry_raw = project.export_records(fields=fields, format='df',
        events=[arm])
    return data_entry_raw

def check(check, error):
    if check:
        error.append(check)

def missing_form(idx,row,field_missing, field_value):
    """
    Generates a report indicating which Forms have not been entered onto redcap
    """
    error = dict()
    #exclude with a value of 1 is excluded
    if math.isnan(row.get('exclude')):
        # visit_ignore____yes with value 1 is ignored
        if row.get('visit_ignore___yes') != 1:
            # form is not missing if form_missing if value nan or zero
            if row.get(field_missing) != 1:
                # for form_date, date is stored as a string
                if type(row.get(field_value)) == float:
                    if math.isnan(row.get(field_value)):
                        error = dict(subject_site_id = idx[0],
                                visit_date = row.get('visit_date'),
                                form_missing = field_missing,
                                event_name = idx[1],
                                error = 'ERROR: Form is missing')
    return error

def np_groove_check(idx,row,field_missing, field_excluded, field_value):
    """
    Checks to see if the Grooveboard NP is missing
    """
    # visit_ignore____yes with value 0 is not ignored
    error = dict()
    if math.isnan(row.get('exclude')):
        if row.get('visit_ignore___yes') == 0:
            # np is not missing if field_missing if value nan or zero
            if row.get(field_excluded) == 0:
                # np is not excluded if field_missing if value nan or zero
                if row.get(field_missing) == 0 or math.isnan(row.get(field_missing)):
                    # for np_date, date is stored as a string
                    if type(row.get(field_value)) == float:
                        # If field is left blank, a NaN is put in it's place
                        if math.isnan(row.get(field_value)):
                            error = dict(subject_site_id = idx[0],
                                visit_date = row.get('visit_date'),
                                np_missing = field_missing,
                                event_name = idx[1],
                                error = 'ERROR: NP is missing.'
                                )
    return error

def fourteen_days_mri_report(idx,row):
    """
    Generates a report indicating which MRI reports have no data after 14 days.
    """
    error = dict()
    #exclude with a value of 1 is excluded
    if math.isnan(row.get('exclude')):
        # visit_ignore____yes with value 1 is ignored
        if row.get('visit_ignore___yes') != 1:
                    if row.get('mrireport_missing') != 1:
                        if type(row.get('mrireport_missing')) == str:
                            if datetime.datetime.strptime(row.get('mrireport_date'),'%Y-%m-%d') == datetime.date.today()-datetime.timedelta(days = 14):
                                error = dict(subject_site_id = idx[0],
                                visit_date = row.get('visit_date'),
                                event_name = idx[1],
                                error = 'ERROR: No MRI data after 14 days')
    return error

def cnp_dob(idx,row):
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

def missing_mri_stroop(idx,row):
    """
    Generate a report indicating which MRI Stroop have not been entered.
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
                                    xnat_sid = row.get('mri_xnat_sid'),
                                    visit_date = row.get('visit_date'),
                                    event_name = idx[1],
                                    error = 'ERROR: MRI Stroop is missing'
                                    )
    return error

def missing_saliva_sample(idx,row,saliva_collected, saliva_date):
    """
    Generate a report indicating which Saliva Samples have not been entered.
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

def visit_data_missing(idx,row):
    """
    Generate a report indicating which Visit Dates are missing.
    """
    error = dict()
    if row.get('exclude') != 1:
        if row.get('visit_ignore___yes') != 1:
            if type(row.get('visit_date')) != str:
                error = dict(subject_site_id = idx[0],
                    event_name = idx[1],
                    error = 'ERROR: Visit date missing.'
                    )
    return error

def wais_score_verification(idx,row):
    """
    Verifies whether the wais_rawscore was computed correctly.
    """
    # visit_ignore____yes with value 0 is not ignored
    error = dict()
    if math.isnan(row.get('exclude')):
        if row.get('visit_ignore___yes') != 1:
            # form is not missing if form_missing if value nan or zero
            if row.get('np_wais4_missing') != 1:
                if row.get('np_wais4_rawscore_computed') == row.get('np_wais4_rawscore_diff(correct)'):
                    if row.get('np_wais4_rawscore_diff(correct)') != 0:
                        error = dict(subject_site_id = idx[0],
                            visit_date = row.get('visit_date'),
                            event_name = idx[1],
                            error = 'ERROR: WAIS score is not verified'
                            )
    return error

def youth_report_sex(idx,row, field_missing, field_sex):
    """
    Checks whether or not sex was entered correctly in the Youth Report
    """
    # visit_ignore____yes with value 0 is not ignored
    error = dict()
    if math.isnan(row.get('exclude')):
        if row.get('visit_ignore___yes') != 1:
            # np is not missing if field_missing if value nan or zero
            if row.get(field_missing) != 1:
                if row.get('sex') != row.get(field_sex):
                    error = dict(subject_site_id = idx[0],
                                visit_date = row.get('visit_date'),
                                event_name = idx[1],
                                field = field_sex,
                                error = 'ERROR: SEX and SEX in YOUTHREPORT do not match.'
                                )
    return error


def main(args):
    project_entry = get_project_entry()
    project_df = data_entry_fields(fields,project_entry,args.visit)
    error = []

    for idx, row in project_df.iterrows():
        for f in form_fields:
            check(missing_form(idx,row,f[0],f[1]),error)
        for np in np_gpeg_fields:
            check(np_groove_check(idx,row,'np_gpeg_missing',np[0],np[1]),error)
        check(fourteen_days_mri_report(idx,row),error)
        check(cnp_dob(idx, row),error)
        check(missing_mri_stroop(idx, row),error)
        for s in saliva_fields:
            check(missing_saliva_sample(idx,row,s[0],s[1]),error)
        check(visit_data_missing(idx,row),error)
        check(wais_score_verification(idx,row),error)
        for f in fields_sex:
            check(youth_report_sex(idx,row,f[0],f[1]),error)

    for e in error:
        if e != 'null':
            #print json.dumps(e, sort_keys=True)
            #print "{}-{}".format(e['subject_site_id'], e['visit_date']), e['error'],e
            sibis.logging("{}-{}".format(e['subject_site_id'], e['visit_date']), e['error'],e_dictionary=e)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-v','--visit',choices=['baseline_visit_arm_1','1y_visit_arm_1'],default='1y_visit_arm_1')
    argv = parser.parse_args()
    sys.exit(main(args=argv))
