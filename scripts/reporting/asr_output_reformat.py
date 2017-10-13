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
excel =pandas.ExcelFile('asr_june2017.xlsx')
data = excel.parse("Sheet1")


today=time.strftime("%m%d%Y")
myfile_name='asr_outcome_reformate_'+today+'.csv'
data = data.rename(columns={'Personal_Strengths_Total':'asr_strength_raw',
'Personal_Strengths_TScore':'asr_strength_t',
'Personal_Strengths_Percentile':'asr_strength_pct',
'Anxious__Depressed_Total':'asr_anxdep_raw',
'Anxious__Depressed_TScore':'asr_anxdep_t',
'Anxious__Depressed_Percentile':'asr_anxdep_pct',
'Withdrawn_Total':'asr_withdrawn_raw',
'Withdrawn_TScore':'asr_withdrawn_t',
'Withdrawn_Percentile':'asr_withdrawn_pct',
'Somatic_Complaints_Total':'asr_somaticraw',
'Somatic_Complaints_TScore':'asr_somatic_t',
'Somatic_Complaints_Percentile':'asr_somatic_pct',
'Thought_Problems_Total':'asr_thought_raw',
'Thought_Problems_TScore':'asr_thought_t',
'Thought_Problems_Percentile':'asr_thought_pct',
'Attention_Problems_Total':'asr_attention_raw',
'Attention_Problems_TScore':'asr_attention_t',
'Attention_Problems_Percentile':'asr_attention_pct',
'Aggressive_Behavior_Total':'asr_aggressive_raw',
'Aggressive_Behavior_TScore':'asr_aggressive_t',
'Aggressive_Behavior_Percentile':'asr_aggressive_pct',
'Rule_Breaking_Behavior_Total':'asr_rulebreak_raw',
'Rule_Breaking_Behavior_TScore':'asr_rulebreak_t',
'Rule_Breaking_Behavior_Percentile':'asr_rulebreak_pct',
'Intrusive_Total':'asr_intrusive_raw',
'Intrusive_TScore':'asr_intrusive_t',
'Intrusive_Percentile':'asr_intrusive_pct',
'Internalizing_Problems_Total':'asr_internal_raw',
'Internalizing_Problems_TScore':'asr_internal_t',
'Internalizing_Problems_Percentile':'asr_internal_pct',
'Externalizing_Problems_Total':'asr_external_raw',
'Externalizing_Problems_TScore':'asr_external_t',
'Externalizing_Problems_Percentile':'asr_external_pct',
'Total_Problems_Total':'asr_totprob_raw',
'Total_Problems_TScore':'asr_totprob_t',
'Total_Problems_Percentile':'asr_totprob_pct',
'Depressive_Problems_Total':'asr_dep_dsm_raw',
'Depressive_Problems_TScore':'asr_dep_dsm_t',
'Depressive_Problems_Percentile':'asr_dep_dsm_pct',
'Anxiety_Problems_Total':'asr_anx_dsm_raw',
'Anxiety_Problems_TScore':'asr_anx_dsm_t',
'Anxiety_Problems_Percentile':'asr_anx_dsm_pct',
'Somatic_Problems_Total':'asr_somat_dsm_raw',
'Somatic_Problems_TScore':'asr_somat_dsm_t',
'Somatic_Problems_Percentile':'asr_somat_dsm_pct',
'Avoidant_Personality_Problems_Total':'asr_avoid_dsm_raw',
'Avoidant_Personality_Problems_TScore':'asr_avoid_dsm_t',
'Avoidant_Personality_Problems_Percentile':'asr_avoid_dsm_pct',
'AD_H_Problems_Total':'asr_adhd_dsm_raw',
'AD_H_Problems_TScore':'asr_adhd_dsm_t',
'AD_H_Problems_Percentile':'asr_adhd_dsm_pct',
'Antisocial_Personality_Total':'asr_antisoc_dsm_raw',
'Antisocial_Personality_TScore':'asr_antisoc_dsm_t',
'Antisocial_Personality_Percentile':'asr_antisoc_dsm_pct',
'Inattention_Problems_Subscale_Total':'asr_inatten_raw',
'Inattention_Problems_Subscale_TScore':'asr_inatten_t',
'Inattention_Problems_Subscale_Percentile':'asr_inatten_pct',
'Hyperactivity_Impulsivity_Problems_Subscale_Total':'asr_hyper_raw',
'Hyperactivity_Impulsivity_Problems_Subscale_TScore':'asr_hyper_t',
'Hyperactivity_Impulsivity_Problems_Subscale_Percentile':'asr_hyper_pct',
'Sluggish_Cognitive_Tempo_Total':'asr_slugcog_raw',
'Sluggish_Cognitive_Tempo_TScore':'asr_slugcog_t',
'Sluggish_Cognitive_Tempo_Percentile':'asr_slugcog_pct',
'Obsessive_Compulsive_Problems_Total':'asr_ocd_raw',
'Obsessive_Compulsive_Problems_TScore':'asr_ocd_t',
'Obsessive_Compulsive_Problems_Percentile':'asr_ocd_pct'})


namelist=['strength_raw',
'strength_t',
'strength_pct',
'anxdep_raw',
'anxdep_t',
'anxdep_pct',
'withdrawn_raw',
'withdrawn_t',
'withdrawn_pct',
'somaticraw',
'somatic_t',
'somatic_pct',
'thought_raw',
'thought_t',
'thought_pct',
'attention_raw',
'attention_t',
'attention_pct',
'aggressive_raw',
'aggressive_t',
'aggressive_pct',
'rulebreak_raw',
'rulebreak_t',
'rulebreak_pct',
'intrusive_raw',
'intrusive_t',
'intrusive_pct',
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
'avoid_dsm_raw',
'avoid_dsm_t',
'avoid_dsm_pct',
'adhd_dsm_raw',
'adhd_dsm_t',
'adhd_dsm_pct',
'antisoc_dsm_raw',
'antisoc_dsm_t',
'antisoc_dsm_pct',
'inatten_raw',
'inatten_t',
'inatten_pct',
'hyper_raw',
'hyper_t',
'hyper_pct',
'slugcog_raw',
'slugcog_t',
'slugcog_pct',
'ocd_raw',
'ocd_t',
'ocd_pct']

colnames2out=list()
for i in namelist:
    colnames2out.append('asr_'+str(i))
colnames_out=['subject','arm','visit','Age','asr_firstname']+colnames2out
data_ysr= data[colnames_out]

myfile = open(myfile_name, 'w')
    


data_ysr.to_csv(myfile_name, index=False)
myfile.close()        
elapsed = (time.time() - start)
print elapsed
