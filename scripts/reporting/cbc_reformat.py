import time
import redcap
import numpy as np
from datetime import datetime
from numpy import genfromtxt
import numpy as np
import pandas as pd
from pandas import DataFrame
import os

api_url = 'https://ncanda.sri.com/redcap/api/'
api_key_entry = os.environ['REDCAP_API_KEY']
project_entry = redcap.Project(api_url, api_key_entry)


additional_columns = ['study_id', 'redcap_event_name',
                      'dob', #'sex',
                      'age', 'mri_xnat_sid']
# note that we don't actually need DOB (since age is calculated for each visit) 
# or sex (because we extract it from study_id)
general_df = project_entry.export_records(fields=additional_columns, format='df')
cbc_df = project_entry.export_records(fields=['study_id'], forms=['parent_report'], format='df')
# filter columns so that they start with parentreport_cbcl_section
# *any* NaN in answers make bpitems uninterpretable -> need to drop them all
# (experiment with thresh<119 to see how many P's are missing one, two, ... answers)
cbc_df_answers = cbc_df.filter(regex=r'^parentreport_cbcl_section').dropna(axis=0, how='any')

# shrink into a single column
cbc_df_answers['bpitems'] = (cbc_df_answers
                             .iloc[:, 0:(len(cbc_df_answers.columns))]
                             .astype(int)
                             .astype(str)
                             .apply(lambda x: "'" + ''.join(x), axis=1))


cbc_df_bpitems = cbc_df_answers.loc[:, ['bpitems']]

# with NaN-containing answers filtered out, grab age and XNAT SID for the surviving records
output_df = pd.merge(general_df, cbc_df_bpitems, 
                     left_index=True, right_index=True, 
                     how='right')

# optional: drop missing age
# output_df = output_df.dropna(subset=['age'])

# Using the fact that pandas will automatically create an index as range(nrows),
# we obtain subjectno instead of creating it ourselves.
# - maybe it would be more pythonic to just assign range(n) to the column.
output_df = output_df.reset_index()
output_df.index.rename('subjectno', inplace=True)
output_df = output_df.reset_index() # get subjectno as a column

# Assign the constant values required by ADM
output_df = output_df.assign(admver=9.1,
                             datatype='raw',
                             dfo='//',
                             formver='2001',
                             dataver='2001',
                             formno='9',
                             formid='9',
                             type='CBC',
                             enterdate=time.strftime("%m/%d/%Y"),
                             compitems="'" + ('9' * 40)
                             )

# Extract gender from study ID
output_df = output_df.assign(gender=lambda x: x.study_id.str.extract(r'([MF])-[0-9]$'))

# Rename columns to be reused
output_df = output_df.rename(columns={'study_id': 'firstname', 
                                      'mri_xnat_sid': 'middlename', 
                                      'redcap_event_name': 'lastname'})

# Rearrange existing columns and fill the non-existent one with NaNs
adm_headers=["admver","datatype","subjectno","id","firstname","middlename","lastname","othername","gender","dob",
             "ethniccode","formver","dataver","formno","formid","type","enterdate","dfo","age","agemonths",
             "educcode","fobcode","fobgender","fparentses","fsubjses","fspouseses","agencycode","clincode",
             "bpitems","compitems","afitems","otheritems","experience","scafitems","facilityco","numchild",
             "hours","months","schoolname","schoolcode","tobacco","drunk","drugs","drinks","ctimecode","ctypecode",
             "early","weeksearly","weight","lb_gram","ounces","infections","nonenglish","slowtalk","worried",
             "spontan","combines","mlp","words162","words310","otherwords","totwords","origin","fudefcode1",
             "fudefcode2","sudefcode1","interviewr","rater","fstatus","usertext","sparentses","ssubjses","cas",
             "casfsscr","das","dasgcascr","kabc","kabcmpcscr","sb5","sb5fsiqscr","wj3cog","wj3cogscr","wais3",
             "wais3scr","wisc4","wisc4scr","wppsi3","wppsi3scr","other1test","othtst1scr","other2test","othtst2scr",
             "other3test","othtst3scr","other1name","other2name","other3name","obstime","rptgrd","medic","medicdesc",
             "dsmcrit","dsmcode1","dsmdiag1","dsmcode2","dsmdiag2","dsmcode3","dsmdiag3","dsmcode4","dsmdiag4",
             "dsmcode5","dsmdiag5","dsmcode6","dsmdiag6","illness","illdesc","speced","sped1","sped2","sped3",
             "sped4","sped5","sped6","sped7","sped8","sped9","sped10","sped10a","sped10b","sped10c","admcatlg",
             "society","cethnic","ceduc","cfob","cagency","cclin","cintervr","crater","cfacilit","ctime","ctype",
             "cschool","cfudef1","cfudef2","csudef1"]
output_df = output_df.reindex(columns=adm_headers)

# Export
output_df.to_csv('cbc_prep_' + time.strftime("%m%d%Y") + '.csv', index=False)
