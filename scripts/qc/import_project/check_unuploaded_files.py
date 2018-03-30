
# coding: utf-8

# This file:
# 
# 1. Loads all available records from the Import Project
# 2. Gathers completion/emptiness features about each record in empty project
# 3. Cross-checks with harvester-generated CSV files to see if they correspond to a non-empty record
# 4. Writes out the files suspected of not having been uploaded to the Import project
# 
# ## To run:
# 
# Ensure that your API key is stored in an environment variable `REDCAP_IMPORT_KEY`.
# 
# ```bash
# source activate ncanda-1.0.0
# jupyter nbconvert --to notebook --execute check_unuploaded_files.ipynb
# # or (equivalently)
# python check_unuploaded_files.py
# ```
# 
# Currently, results are written into `not_in_import.txt`.
# 
# ## TODO: Converting to CLI
# - Use sibis config for API key
# - Print to stdin or optional `-o` file
# - Should extract out load_all and chunked_export to general utilities

# ## 1. Loading all available records

# In[1]:


import pandas as pd
import os
import redcap as rc
import numpy as np


# In[2]:


pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)


# In[3]:


REDCAP_IMPORT_KEY = os.environ['REDCAP_IMPORT_KEY']
api_url = 'https://ncanda.sri.com/redcap/api/'
api = rc.Project(api_url, REDCAP_IMPORT_KEY)
primary_key = api.def_field


# In[4]:


meta = api.export_metadata(format='df')
forms = meta.form_name.unique().tolist()
forms


# In[5]:


# Taken from http://pycap.readthedocs.io/en/latest/deep.html#dealing-with-large-exports
# and adapted to scope down to forms
def chunked_export(project, form, chunk_size=100):
    def chunks(l, n):
        """Yield successive n-sized chunks from list l"""
        for i in xrange(0, len(l), n):
            yield l[i:i+n]
    record_list = project.export_records(fields=[project.def_field])
    records = [r[project.def_field] for r in record_list]
    #print "Total records: %d" % len(records)
    try:
        response = None
        record_count = 0
        for record_chunk in chunks(records, chunk_size):
            record_count = record_count + chunk_size
            #print record_count
            chunked_response = project.export_records(records=record_chunk, 
                                                      fields=[project.def_field],
                                                      forms=[form], format='df')
            if response is not None:
                response = pd.concat([response, chunked_response], axis=0)
            else:
                response = chunked_response
    except rc.RedcapError:
        msg = "Chunked export failed for chunk_size={:d}".format(chunk_size)
        raise ValueError(msg)
    else:
        return response


# In[6]:


def load_form(api, form_name):
    print form_name
    # 1. Standard load attempt
    try:
        print "Trying standard export"
        return api.export_records(fields=[api.def_field],
                                  forms=[form_name],
                                  format='df')
    except rc.RedcapError:
        pass
    
    # 2. Chunked load with chunk size of 1000
    try:
        print "Trying chunked export, 1000 records at a time"
        return chunked_export(api, form_name, 1000)
    except rc.RedcapError:
        pass
    
    # 2. Chunked load with default chunk size
    try:
        print "Trying chunked export, default chunk size (100)"
        return chunked_export(api, form_name)
    except rc.RedcapError:
        pass
    
    # 3. Chunked load with tiny chunk
    try:
        print "Trying chunked export with tiny chunks (10)"
        return chunked_export(api, form_name, 10)
    except rc.RedcapError:
        print "Giving up"
        return None


# In[7]:


all_forms = {form_name: load_form(api, form_name) for form_name in forms}


# ## 2. Checking emptiness

# In[8]:


# Apply to DF to get all empty records
def is_empty_record(row, form_name, drop_columns=None):
    # 1. check complete
    complete_field = form_name + '_complete'
    is_incomplete = row[complete_field] == 0  # TODO: maybe complete_field not in [1, 2] to catch NaNs?
    
    # 2. count up NaNs
    if drop_columns:
        drop_columns.append(complete_field)
    else:
        drop_columns = [complete_field]
    non_nan_count = row.drop(drop_columns).notnull().sum()
    
    return pd.Series({'incomplete': is_incomplete, 'non_nan_count': non_nan_count})


# In[9]:


all_forms_flagged = {form_name: df.apply(lambda row: is_empty_record(row, form_name), axis=1) 
                     for form_name, df 
                     in all_forms.items()}


# In[10]:


not_uploaded_by_form = {form_name: df.query('incomplete and non_nan_count == 0').index.tolist()
                        for form_name, df in all_forms_flagged.items()}


# In[11]:


{form: len(x) for form, x in not_uploaded_by_form.items()}


# In[12]:


incomplete_with_data = {form_name: df.query('incomplete and non_nan_count > 0')
                        for form_name, df in all_forms_flagged.items()}


# In[13]:


{form: len(x) for form, x in incomplete_with_data.items()}


# In[14]:


complete_without_data = {form_name: df.query('not incomplete and non_nan_count == 0').index.tolist()
                         for form_name, df in all_forms_flagged.items()}


# In[15]:


{form: len(x) for form, x in complete_without_data.items()}


# # Cross-checking with `harvester`-generated CSVs

# In[16]:


all_forms = {
    # Forms for Arm 1: Standard Protocol  
    'dd100': 'delayed_discounting_100',
    'dd1000': 'delayed_discounting_1000',

    'pasat': 'paced_auditory_serial_addition_test_pasat',
    'stroop': 'stroop',
    
    'ssaga_youth': 'ssaga_youth',
    'ssaga_parent': 'ssaga_parent',
    'youthreport1': 'youth_report_1',
    'youthreport1b': 'youth_report_1b',
    'youthreport2': 'youth_report_2',
    'parentreport': 'parent_report',
    
    'mrireport': 'mri_report',
    'plus': 'participant_last_use_summary',
    
    'myy': 'midyear_youth_interview',
    
    'lssaga1_youth': 'limesurvey_ssaga_part_1_youth',
    'lssaga2_youth': 'limesurvey_ssaga_part_2_youth',
    'lssaga3_youth': 'limesurvey_ssaga_part_3_youth',
    'lssaga4_youth': 'limesurvey_ssaga_part_4_youth',
    
    'lssaga1_parent': 'limesurvey_ssaga_part_1_parent',
    'lssaga2_parent': 'limesurvey_ssaga_part_2_parent',
    'lssaga3_parent': 'limesurvey_ssaga_part_3_parent',
    'lssaga4_parent': 'limesurvey_ssaga_part_4_parent',

    # Forms for Arm 3: Sleep Studies
    'sleepeve': 'sleep_study_evening_questionnaire',
    'sleeppre': 'sleep_study_presleep_questionnaire',
    'sleepmor': 'sleep_study_morning_questionnaire',

    # Forms for Recovery project
    'recq': 'recovery_questionnaire',
    
    # Forms for UCSD
    'parent': 'ssaga_parent',
    'youth': 'ssaga_youth',
    'deldisc': 'delayed_discounting'
}


# In[17]:


def get_ID_from_filename(fname):
    # strip file extension
    # strip -100[0]
    import re
    return re.sub(r'-?(1000?|fields)?\.csv$', '', fname).strip()

def get_record_IDs_for_form(form, files, folder_path = None):
    if form == "delayed_discounting":
        # Cannot approach straightforwardly because filename violates convention 
        # - need to process $100 and $1000 as separate forms, even though they're in the same folder
        dd100_records = [f for f in files if f.endswith("-100.csv")]
        dd1000_records = [f for f in files if f.endswith("-1000.csv")]
        dd100 = get_record_IDs_for_form(form + '_100', dd100_records, folder_path)
        dd1000 = get_record_IDs_for_form(form + '_1000', dd1000_records, folder_path)
        return dict(dd100.items() + dd1000.items())
    else:
        records = [get_ID_from_filename(f) for f in files]
        if folder_path is not None:
            files = [folder_path + '/' + f for f in files]
        return {form: dict(zip(files, records))}


# In[18]:


# Extract records from all the files and keep file->record_id associations
# TODO: Make a data frame on the first pass
records_by_form = {}
for root, subdirs, files in os.walk('/fs/storage/laptops/imported'):
    csv_files = [f for f in files if (".csv" in f and "-fields" not in f)]
    root_parts = root.split('/')
    current_folder = root_parts[-1]
    if subdirs or not csv_files:
        print "passing %s" % root
        continue
    else:
        print "entering %s" % root
        
        try:
            form = all_forms[current_folder]
        except KeyError as e:
            print "Couldn't find %s in `all_forms`. Skipping." % current_folder
            continue
    # Create a dict of files -> record IDs
    all_records = get_record_IDs_for_form(form, csv_files, folder_path=root)
    for record_form, file_records in all_records.iteritems():
        if record_form in records_by_form:
            records_by_form[record_form].update(file_records)
        else:
            records_by_form[record_form] = file_records
    #record_ids = [get_ID_from_filename(f) for f in csv_files]


# 2. Within each form, iterate through the files + record_IDs and check if the record ID is non-empty in the previously collected dataframe: 

# In[20]:


# Remake the record_by_form into a data frame
file_df = pd.DataFrame()
for form, file_record_ids in records_by_form.iteritems():
    form_df = pd.DataFrame.from_dict(file_record_ids, orient='index')
    form_df.columns = ['record_id']
    form_df['form'] = form
    file_df = pd.concat([file_df, form_df])


# In[23]:


def get_flag_info(row):
    try:
        return all_forms_flagged[row['form']].loc[row['record_id']]
    except KeyError:
        return pd.Series({'form': row['form'], 'incomplete': np.nan, 'non_nan_count': 0})


# In[24]:


#file_df.apply(lambda row: all_forms_flagged[row['form']].loc[row['record_id']], axis=1)
file_counts = file_df.apply(get_flag_info, axis=1)


# In[26]:


not_uploaded_files = file_counts.query('non_nan_count <= 0').index.tolist()


# In[27]:


print len(not_uploaded_files)


# In[28]:


with open('not_in_import.txt', 'wb') as f:
    f.write("\n".join(not_uploaded_files))

