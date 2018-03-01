import time
start = time.time()
import redcap
import array
import string
import csv
import numpy
import sys
import glob
from datetime import datetime
import numpy
from numpy import genfromtxt
import numpy as np
import pandas
from pandas import DataFrame

data = pandas.read_excel('aseba_prep/new_script/ysr_scored_partial.xlsx', 
			 sheet_name=0)  # return first sheet

today=time.strftime("%m%d%Y")
myfile_name='aseba_prep/ysr_outcome_reformate_'+today+'.csv'
data = data.rename(columns={
    'ysr_middlename': 'subject',
    'ysr_lastname': 'visit',
    'ysr_firstname': 'study_id',
    'Anxious__Depressed_Total': 'ysr_anxdep_raw',
    'Anxious__Depressed_TScore': 'ysr_anxdep_t',
    'Anxious__Depressed_Percentile': 'ysr_anxdep_pct',
    'Withdrawn__Depressed_Total': 'ysr_withdep_raw',
    'Withdrawn__Depressed_TScore': 'ysr_withdep_t',
    'Withdrawn__Depressed_Percentile': 'ysr_withdep_pct',
    'Somatic_Complaints_Total': 'ysr_somatic_raw',
    'Somatic_Complaints_TScore': 'ysr_somatic_t',
    'Somatic_Complaints_Percentile': 'ysr_somatic_pct',
    'Social_Problems_Total': 'ysr_social_raw',
    'Social_Problems_TScore': 'ysr_social_t',
    'Social_Problems_Percentile': 'ysr_social_pct',
    'Thought_Problems_Total': 'ysr_thought_raw',
    'Thought_Problems_TScore': 'ysr_thought_t',
    'Thought_Problems_Percentile': 'ysr_thought_pct',
    'Attention_Problems_Total': 'ysr_attention_raw',
    'Attention_Problems_TScore': 'ysr_attention_t',
    'Attention_Problems_Percentile': 'ysr_attention_pct',
    'Rule_Breaking_Behavior_Total': 'ysr_rulebrk_raw',
    'Rule_Breaking_Behavior_TScore': 'ysr_rulebrk_t',
    'Rule_Breaking_Behavior_Percentile': 'ysr_rulebrk_pct',
    'Aggressive_Behavior_Total': 'ysr_aggress_raw',
    'Aggressive_Behavior_TScore': 'ysr_aggress_t',
    'Aggressive_Behavior_Percentile': 'ysr_aggress_pct',
    'Internalizing_Problems_Total': 'ysr_internal_raw',
    'Internalizing_Problems_TScore': 'ysr_internal_t',
    'Internalizing_Problems_Percentile': 'ysr_internal_pct',
    'Externalizing_Problems_Total': 'ysr_external_raw',
    'Externalizing_Problems_TScore': 'ysr_external_t',
    'Externalizing_Problems_Percentile': 'ysr_external_pct',
    'Total_Problems_Total': 'ysr_totprob_raw',
    'Total_Problems_TScore': 'ysr_totprob_t',
    'Total_Problems_Percentile': 'ysr_totprob_pct',
    'Depressive_Problems_Total': 'ysr_dep_dsm_raw',
    'Depressive_Problems_TScore': 'ysr_dep_dsm_t',
    'Depressive_Problems_Percentile': 'ysr_dep_dsm_pct',
    'Anxiety_Problems_Total': 'ysr_anx_dsm_raw',
    'Anxiety_Problems_TScore': 'ysr_anx_dsm_t',
    'Anxiety_Problems_Percentile': 'ysr_anx_dsm_pct',
    'Somatic_Problems_Total': 'ysr_somat_dsm_raw',
    'Somatic_Problems_TScore': 'ysr_somat_dsm_t',
    'Somatic_Problems_Percentile': 'ysr_somat_dsm_pct',
    'Attention_Deficit__Hyperactivity_Problems_Total': 'ysr_adhd_dsm_raw',
    'Attention_Deficit__Hyperactivity_Problems_TScore': 'ysr_adhd_dsm_t',
    'Attention_Deficit__Hyperactivity_Problems_Percentile': 'ysr_adhd_dsm_pct',
    'Oppositional_Defiant_Problems_Total': 'ysr_odd_dsm_raw',
    'Oppositional_Defiant_Problems_TScore': 'ysr_odd_dsm_t',
    'Oppositional_Defiant_Problems_Percentile': 'ysr_odd_dsm_pct',
    'Conduct_Problems_Total': 'ysr_cd_dsm_raw',
    'Conduct_Problems_TScore': 'ysr_cd_dsm_t',
    'Conduct_Problems_Percentile': 'ysr_cd_dsm_pct',
    'Obsessive_Compulsive_Problems_Total': 'ysr_ocd_raw',
    'Obsessive_Compulsive_Problems_TScore': 'ysr_ocd_t',
    'Obsessive_Compulsive_Problems_Percentile': 'ysr_ocd_pct',
    'Stress_Problems_Total': 'ysr_stress_raw',
    'Stress_Problems_TScore': 'ysr_stress_t',
    'Stress_Problems_Percentile': 'ysr_stress_pct',
    'Positive_Qualities_Total': 'ysr_positive_raw',
    'Positive_Qualities_TScore': 'ysr_positive_t',
    'Positive_Qualities_Percentile': 'ysr_positive_pct'})


namelist=['anxdep_raw',
'anxdep_t',
'anxdep_pct',
'withdep_raw',
'withdep_t',
'withdep_pct',
'somatic_raw',
'somatic_t',
'somatic_pct',
'social_raw',
'social_t',
'social_pct',
'thought_raw',
'thought_t',
'thought_pct',
'attention_raw',
'attention_t',
'attention_pct',
'rulebrk_raw',
'rulebrk_t',
'rulebrk_pct',
'aggress_raw',
'aggress_t',
'aggress_pct',
'internal_raw',
'internal_t',
'internal_pct',
'external_raw',
'external_t',
'external_pct',
'totprob_raw',
'totprob_t',
'totprob_pct',
'dep_dsm_raw',
'dep_dsm_t',
'dep_dsm_pct',
'anx_dsm_raw',
'anx_dsm_t',
'anx_dsm_pct',
'somat_dsm_raw',
'somat_dsm_t',
'somat_dsm_pct',
'adhd_dsm_raw',
'adhd_dsm_t',
'adhd_dsm_pct',
'odd_dsm_raw',
'odd_dsm_t',
'odd_dsm_pct',
'cd_dsm_raw',
'cd_dsm_t',
'cd_dsm_pct',
'ocd_raw',
'ocd_t',
'ocd_pct',
'stress_raw',
'stress_t',
'stress_pct',
'positive_raw',
'positive_t',
'positive_pct']

# Modify the metadata columns
data['arm'] = 'standard'
data['visit'] = data['visit'].str.replace('_arm_1', '')

colnames2out=list()
for i in namelist:
    colnames2out.append('ysr_'+str(i))
colnames_out = ['subject', 'arm', 'visit'] + colnames2out
data_ysr= data[colnames_out]

myfile = open(myfile_name, 'w')

data_ysr.to_csv(myfile_name, index=False)
myfile.close()        
elapsed = (time.time() - start)
print elapsed
