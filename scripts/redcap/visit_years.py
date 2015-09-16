import time
start = time.time()
import redcap
from datetime import datetime
import csv
import pandas
from pandas import DataFrame
import array
import string
import numpy
import sys
import glob
from numpy import genfromtxt
import numpy as np
import os


summary_key_file = open(os.path.join( os.path.expanduser("~"), '.server_config', 'redcap-dataentry-token'), 'r')

summary_api_key = summary_key_file.read().strip()
project_entry  = redcap.Project('https://ncanda.sri.com/redcap/api/', summary_api_key, verify_ssl=False)


data_entry_raw= DataFrame(project_entry.export_records(fields=['study_id','redcap_event_name','dob','sex','exclude','visit_ignore','visit_date','visit_ignore_why','visit_ignore_why_other',
                 'visit_notes','np_notes','clin_notes','mri_t1_date','mri_dti_date','mri_rsfmri_date','mri_xnat_sid','mri_xnat_eids']))



#baseline
baseline_raw=data_entry_raw.loc[data_entry_raw['redcap_event_name'] == "Baseline visit (Arm 1: Standard Protocol)"]
baseline=baseline_raw[['study_id','redcap_event_name','dob','sex','exclude','visit_date','visit_ignore___yes']]
baseline = baseline.rename(columns={'redcap_event_name': 'baseline', 'visit_date': 'baseline_date', 'visit_ignore___yes': 'baseline_ignore'})
#6 Month
Month6_raw=data_entry_raw.loc[data_entry_raw['redcap_event_name'] == "6-month follow-up (Arm 1: Standard Protocol)"]
Month6=Month6_raw[['study_id','redcap_event_name','visit_date','visit_ignore___yes']]
Month6 = Month6.rename(columns={'redcap_event_name': 'Month6', 'visit_date': 'Month6_date', 'visit_ignore___yes': 'Month6_ignore'})

#year1
year1_raw=data_entry_raw.loc[data_entry_raw['redcap_event_name'] == "1y visit (Arm 1: Standard Protocol)"]
year1=year1_raw[['study_id','redcap_event_name','visit_date','visit_ignore___yes','visit_ignore_why','visit_ignore_why_other',
                 'visit_notes','np_notes','clin_notes','mri_t1_date','mri_dti_date','mri_rsfmri_date','mri_xnat_sid','mri_xnat_eids']]
year1 = year1.rename(columns={'redcap_event_name': 'Year1', 'visit_date': 'Year1_date', 'visit_ignore___yes': 'Year1_ignore',
                              'visit_ignore_why' : 'Year1_ignore_reason','visit_ignore_why_other':'Year1_ignore_reason_other',
                              'visit_notes': 'Year1_notes','np_notes': 'Year1_np_notes','clin_notes': 'Year1_clin_notes',
                              'mri_t1_date': 'Year1_t1_date','mri_dti_date': 'Year1_dti_date','mri_rsfmri_date': 'Year1_fmri_date',
                              'mri_xnat_sid':'Year1_xnat_sid','mri_xnat_eids': 'Year1_xnat_eids'})

#18 Month
Month18_raw=data_entry_raw.loc[data_entry_raw['redcap_event_name'] == "18-month follow-up (Arm 1: Standard Protocol)"]
Month18=Month18_raw[['study_id','redcap_event_name','visit_date','visit_ignore___yes']]
Month18 = Month18.rename(columns={'redcap_event_name': 'Month18', 'visit_date': 'Month18_date', 'visit_ignore___yes': 'Month18_ignore'})

#year2
year2_raw=data_entry_raw.loc[data_entry_raw['redcap_event_name'] == "2y visit (Arm 1: Standard Protocol)"]
year2=year2_raw[['study_id','redcap_event_name','visit_date','visit_ignore___yes','visit_ignore_why','visit_ignore_why_other',
                 'visit_notes','np_notes','clin_notes','mri_t1_date','mri_dti_date','mri_rsfmri_date','mri_xnat_sid','mri_xnat_eids']]
year2 = year2.rename(columns={'redcap_event_name': 'Year2', 'visit_date': 'Year2_date', 'visit_ignore___yes': 'Year2_ignore',
                              'visit_ignore_why' : 'Year2_ignore_reason','visit_ignore_why_other':'Year2_ignore_reason_other',
                              'visit_notes': 'Year2_notes','np_notes': 'Year2_np_notes','clin_notes': 'Year2_clin_notes',
                              'mri_t1_date': 'Year2_t1_date','mri_dti_date': 'Year2_dti_date','mri_rsfmri_date': 'Year2_fmri_date',
                              'mri_xnat_sid':'Year2_xnat_sid','mri_xnat_eids': 'Year2_xnat_eids'})




all_visit=pandas.merge(baseline, year1, how='left', on=['study_id'])
all_visit=pandas.merge(all_visit, year2, how='left', on=['study_id'])





today=time.strftime("%m%d%Y")
myfile_name='visit_date_'+today+'.csv'
myfile = open(myfile_name, 'w')

#aa=DataFrame(columns=[list2check,id,import_date,import_date_test,import_exclude])
all_visit.to_csv(myfile_name, index=False)

#myfile.close()
elapsed = (time.time() - start)
print elapsed
#wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
#wr.writerow(subset)

