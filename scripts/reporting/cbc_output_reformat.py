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




print 'Please Specify a file name: ASR, YSR, CBC'
excel =pandas.ExcelFile('cbc_june2017.xlsx')
data = excel.parse("CBCL_6_18")


today=time.strftime("%m%d%Y")
myfile_name='cbc_outcome_reformate_'+today+'.csv'
data = data.rename(columns={'Anxious__Depressed_Total':'cbcl_anxdep_raw',
'Anxious__Depressed_TScore':'cbcl_anxdep_t',
'Anxious__Depressed_Percentile':'cbcl_anxdep_pct',
'Withdrawn__Depressed_Total':'cbcl_withdep_raw',
'Withdrawn__Depressed_TScore':'cbcl_withdep_t',
'Withdrawn__Depressed_Percentile':'cbcl_withdep_pct',
'Somatic_Complaints_Total':'cbcl_somatic_raw',
'Somatic_Complaints_TScore':'cbcl_somatic_t',
'Somatic_Complaints_Percentile':'cbcl_somatic_pct',
'Social_Problems_Total':'cbcl_social_raw',
'Social_Problems_TScore':'cbcl_social_t',
'Social_Problems_Percentile':'cbcl_social_pct',
'Thought_Problems_Total':'cbcl_thought_raw',
'Thought_Problems_TScore':'cbcl_thought_t',
'Thought_Problems_Percentile':'cbcl_thought_pct',
'Attention_Problems_Total':'cbcl_atten_raw',
'Attention_Problems_TScore':'cbcl_atten_t',
'Attention_Problems_Percentile':'cbcl_atten_pct',
'Rule_Breaking_Behavior_Total':'cbcl_rulebrk_raw',
'Rule_Breaking_Behavior_TScore':'cbcl_rulebrk_t',
'Rule_Breaking_Behavior_Percentile':'cbcl_rulebrk_pct',
'Aggressive_Behavior_Total':'cbcl_aggress_raw',
'Aggressive_Behavior_TScore':'cbcl_aggress_t',
'Aggressive_Behavior_Percentile':'cbcl_aggress_pct',
'Internalizing_Problems_Total':'cbcl_internal_raw',
'Internalizing_Problems_TScore':'cbcl_internal_t',
'Internalizing_Problems_Percentile':'cbcl_internal_pct',
'Externalizing_Problems_Total':'cbcl_external_raw',
'Externalizing_Problems_TScore':'cbcl_external_t',
'Externalizing_Problems_Percentile':'cbcl_external_pct',
'Total_Problems_Total':'cbcl_totprob_raw',
'Total_Problems_TScore':'cbcl_totprob_t',
'Total_Problems_Percentile':'cbcl_totprob_pct',
'Depressive_Problems_Total':'cbcl_dep_dsm_raw',
'Depressive_Problems_TScore':'cbcl_dep_dsm_t',
'Depressive_Problems_Percentile':'cbcl_dep_dsm_pct',
'Anxiety_Problems_Total':'cbcl_anx_dsm_raw',
'Anxiety_Problems_TScore':'cbcl_anx_dsm_t',
'Anxiety_Problems_Percentile':'cbcl_anx_dsm_pct',
'Somatic_Problems_Total':'cbcl_somat_dsm_raw',
'Somatic_Problems_TScore':'cbcl_somat_dsm_t',
'Somatic_Problems_Percentile':'cbcl_somat_dsm_pct',
'Attention_Deficit__Hyperactivity_Problems_Total':'cbcl_adhd_dsm_raw',
'Attention_Deficit__Hyperactivity_Problems_TScore':'cbcl_adhd_dsm_t',
'Attention_Deficit__Hyperactivity_Problems_Percentile':'cbcl_adhd_dsm_pct',
'Oppositional_Defiant_Problems_Total':'cbcl_odd_dsm_raw',
'Oppositional_Defiant_Problems_TScore':'cbcl_odd_dsm_t',
'Oppositional_Defiant_Problems_Percentile':'cbcl_odd_dsm_pct',
'Conduct_Problems_Total':'cbcl_cd_dsm_raw',
'Conduct_Problems_TScore':'cbcl_cd_dsm_t',
'Conduct_Problems_Percentile':'cbcl_cd_dsm_pct',
'Sluggish_Cognitive_Tempo_Total':'cbcl_slugcog_raw',
'Sluggish_Cognitive_Tempo_TScore':'cbcl_slugcog_t',
'Sluggish_Cognitive_Tempo_Percentile':'cbcl_slugcog_pct',
'Obsessive_Compulsive_Problems_Total':'cbcl_ocd_raw',
'Obsessive_Compulsive_Problems_TScore':'cbcl_ocd_t',
'Obsessive_Compulsive_Problems_Percentile':'cbcl_ocd_pct',
'Stress_Problems_Total':'cbcl_stress_raw',
'Stress_Problems_TScore':'cbcl_stress_t',
'Stress_Problems_Percentile':'cbcl_stress_pct'})


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
'atten_raw',
'atten_t',
'atten_pct',
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
'slugcog_raw',
'slugcog_t',
'slugcog_pct',
'ocd_raw',
'ocd_t',
'ocd_pct',
'stress_raw',
'stress_t',
'stress_pct']

colnames2out=list()
for i in namelist:
    colnames2out.append('cbcl_'+str(i))
colnames_out=['subject','arm','visit','Age','cbc_firstname']+colnames2out
data_ysr= data[colnames_out]

myfile = open(myfile_name, 'w')
    


data_ysr.to_csv(myfile_name, index=False)
myfile.close()        
elapsed = (time.time() - start)
print elapsed
