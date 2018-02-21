import time
import redcap as rc
import pandas as pd
import os

api_url = 'https://ncanda.sri.com/redcap/api/'
api_key_entry = os.environ['REDCAP_API_KEY']
project_entry = rc.Project(api_url, api_key_entry)

additional_columns = ['study_id', 'redcap_event_name',
                      'dob',  # 'sex',
                      'age', 'mri_xnat_sid']
# note that we don't actually need DOB (since age is calculated for each visit) 
# or sex (because we extract it from study_id)
general_df = project_entry.export_records(fields=additional_columns, 
                                          format='df')
general_df = general_df.round({'age': 0}).dropna(subset=['age'])
general_df['age'] = general_df['age'].astype(int)

ysr_df = project_entry.export_records(fields=['study_id'],
                                      forms=['youth_report_1b'], format='df')
# filter columns so that they start with youthreport1_asr_section
# only keep rows that have at least 100 responses
ysr_df_answers = (ysr_df.filter(regex=r'^youthreport1_ysr_section')
                  .dropna(axis=0, how='any', thresh=100)
                  .fillna(value=9))

# shrink into a single column
ysr_df_answers['bpitems'] = (ysr_df_answers
                             .iloc[:, 0:(len(ysr_df_answers.columns))]
                             .astype(int)
                             .astype(str)
                             .apply(lambda x: "'" + ''.join(x), axis=1))

ysr_df_bpitems = ysr_df_answers.loc[:, ['bpitems']]

# with NaN-containing answers filtered out, grab age and XNAT SID for the
# surviving records
output_df = pd.merge(general_df, ysr_df_bpitems, 
                     left_index=True, right_index=True, 
                     how='inner')

# Using the fact that pandas will automatically create an index as
# range(nrows), we obtain subjectno instead of creating it ourselves.
# - maybe it would be more pythonic to just assign range(n) to the column.
output_df = output_df.reset_index()
output_df.index.rename('subjectno', inplace=True)
output_df = output_df.reset_index()  # get subjectno as a column

# Assign contant values
output_df = output_df.assign(admver=9.1,
                             datatype='raw',
                             dfo='//',
                             formver='2001',
                             dataver='2001',
                             formno='13',
                             formid='13',
                             type='YSR',
                             enterdate=time.strftime("%m/%d/%Y"),
                             compitems="'" + ('9' * 36)
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
output_df = output_df.reindex(columns = adm_headers)
output_df.to_csv('ysr_prep_' + time.strftime("%m%d%Y") + '.csv', index=False)
