from __future__ import print_function

# coding: utf-8

# In[ ]:


import pandas as pd
import os
import redcap as rc
import numpy as np
import sibispy
from sibispy import sibislogger as slog
import sys


# In[ ]:


pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)


# # 1. Load data

# In[ ]:


session = sibispy.Session()
if not session.configure():
    sys.exit()

slog.init_log(None, None, 
              'QC: Check all harvester-prepared CSVs are uploaded', 
              'laptop_import_check', None)
slog.startTimer1()

# Setting specific constants for this run of QC
api = session.connect_server('import_laptops', True)
primary_key = api.def_field


# In[ ]:


meta = api.export_metadata(format='df')
form_names = meta.form_name.unique().tolist()
form_names


# In[ ]:


#form_names_subset = [f for f in form_names if not f.startswith('limesurvey')]
form_names_subset = form_names
form_names_subset


# In[ ]:


# Taken from http://pycap.readthedocs.io/en/latest/deep.html#dealing-with-large-exports
# and adapted to scope down to forms
def chunked_export(project, form, chunk_size=100, verbose=True):
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
                                                      forms=[form], 
                                                      format='df',
                                                      df_kwargs={'low_memory': False})
            if response is not None:
                response = pd.concat([response, chunked_response], axis=0)
            else:
                response = chunked_response
    except rc.RedcapError:
        msg = "Chunked export failed for chunk_size={:d}".format(chunk_size)
        raise ValueError(msg)
    else:
        return response


# In[ ]:


def load_form(api, form_name, verbose=True):
    if verbose:
        print(form_name)
    
    # 1. Standard load attempt
    # try:
    #     print "Trying standard export"
    #     return api.export_records(fields=[api.def_field],
    #                               forms=[form_name],
    #                               format='df',
    #                               df_kwargs={'low_memory': False})
    # except (ValueError, rc.RedcapError, pd.io.common.EmptyDataError):
    #     pass
    try:
        print("Trying chunked export, 5000 records at a time")
        return chunked_export(api, form_name, 5000)
    except (ValueError, rc.RedcapError, pd.io.common.EmptyDataError):
        pass
    
    # 2. Chunked load with chunk size of 1000
    try:
        print("Trying chunked export, 1000 records at a time")
        return chunked_export(api, form_name, 1000)
    except (ValueError, rc.RedcapError, pd.io.common.EmptyDataError):
        pass
    
    # 2. Chunked load with default chunk size
    try:
        print("Trying chunked export, default chunk size (100)")
        return chunked_export(api, form_name, 100)
    except (ValueError, rc.RedcapError, pd.io.common.EmptyDataError):
        pass
    
    # 3. Chunked load with tiny chunk
    try:
        print("Trying chunked export with tiny chunks (10)")
        return chunked_export(api, form_name, 10)
    except (ValueError, rc.RedcapError, pd.io.common.EmptyDataError):
        print("Giving up")
        return None

def load_form_with_primary_key(api, form_name, verbose=True):
    df = load_form(api, form_name, verbose)
    if df is not None:
        return df.set_index(api.def_field)


# In[ ]:


all_data = {form_name: load_form_with_primary_key(api, form_name) for form_name in form_names_subset}


# # 2. Extract emptiness statistic from Import records

# In[ ]:


def count_non_nan_rowwise(df, form_name=None, drop_column=None):
    """ A more efficient method of checking non-NaN values """
    # 1. check complete
    if form_name:
        complete_field = form_name + '_complete'
        if drop_columns:
            drop_columns.append(complete_field)
        else:
            drop_columns = [complete_field]
    if drop_columns is None:
        drop_columns = []
    
    # 2. count up NaNs
    return df.drop(drop_columns, axis=1).notnull().sum(axis=1)


# In[ ]:


# Apply to DF to get all empty records
def set_emptiness_flags(row, form_name, drop_columns=None):
    # 1. check complete
    complete_field = form_name + '_complete'
    #is_incomplete = row[complete_field] == 0  # TODO: maybe complete_field not in [1, 2] to catch NaNs?
    
    # 2. count up NaNs
    if drop_columns:
        drop_columns.append(complete_field)
    else:
        drop_columns = [complete_field]
    # NOTE: This will only work for a Series
    # NOTE: For a full Data Frame, use df.drop(drop_columns, axis=1).notnull().sum(axis=1)
    non_nan_count = row.drop(drop_columns).notnull().sum()
    
    return pd.Series({'completion_status': row[complete_field], 'non_nan_count': non_nan_count})


# In[ ]:


emptiness_df = {form_name: all_data[form_name].apply(lambda x: set_emptiness_flags(x, form_name), axis=1) 
                for form_name in all_data.keys() 
                if all_data[form_name] is not None}
#all_data['recovery_questionnaire'].apply(lambda x: set_emptiness_flags(x, 'recovery_questionnaire'), axis=1)


# In[ ]:


for form_name in emptiness_df.keys():
    emptiness_df[form_name]['form'] = form_name
all_forms_emptiness = pd.concat(emptiness_df.values())
all_forms_emptiness.shape


# # 3. Load files

# In[ ]:


short_to_long = {
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


# In[ ]:


files_df = pd.DataFrame(columns=["file", "path", "form"])
records = []
record_paths = []
for root, subdirs, files in os.walk('/fs/storage/laptops/imported'):
    csv_files = [f for f in files if (f.endswith(".csv") and not f.endswith("-fields.csv"))]
    if csv_files:
        folder_df = pd.DataFrame(columns=["file", "path", "form"])
        folder_df['file'] = csv_files
        folder_df['path'] = [root + "/" + f for f in csv_files]
        
        root_parts = root.split('/')
        current_folder = root_parts[-1]
        try:
            form = short_to_long[current_folder]
            if form not in form_names_subset:
                continue
            else:
                folder_df['form'] = form
                files_df = pd.concat([files_df, folder_df])
            
        except KeyError as e:
            continue
files_df.set_index("path", inplace=True)


# In[ ]:


def getRecordIDFromFile(row):
    import re
    bare_file = re.sub(r"\.csv$", "", row["file"])
    if row["form"] == "delayed_discounting":
        bare_file = re.sub("-1000?$", "", bare_file)
    return bare_file
files_df["record_id"] = files_df.apply(getRecordIDFromFile, axis=1)
files_df.head()


# In[ ]:


def fixFormName(row):
    import re
    if row["form"] == "delayed_discounting":
        if re.search(r"-100\.csv$", row["file"]):
            return "delayed_discounting_100"
        elif re.search(r"-1000\.csv$", row["file"]):
            return "delayed_discounting_1000"
        else:
            return "delayed_discounting"
    else:
        return row["form"]


# In[ ]:


files_df["form"] = files_df.apply(fixFormName, axis=1)


# In[ ]:


all_forms_emptiness.head()


# In[ ]:


files_in_redcap = pd.merge(files_df.reset_index(),
                           all_forms_emptiness.reset_index(), 
                           on=["record_id", "form"], 
                           how="outer")


# In[ ]:


files_in_redcap.head()


# # 4. Get results
# ## Files that weren't matched at all

# In[ ]:


files_in_redcap.loc[files_in_redcap.completion_status.isnull()]


# ## Files that were matched but have blank forms

# In[ ]:


files_in_redcap.loc[files_in_redcap['path'].notnull() & (files_in_redcap['non_nan_count'] == 0)]


# In[ ]:


def check_if_file_empty(row):
    contents = pd.read_csv(row['path'])
    return contents.dropna(axis="columns").shape[1]


# In[ ]:


(files_in_redcap
 .loc[files_in_redcap['path'].notnull() & 
      (files_in_redcap['non_nan_count'] == 0)]
 .apply(check_if_file_empty, axis=1))


# ## Records that don't match harvester CSV files

# In[ ]:


files_in_redcap.loc[files_in_redcap['path'].isnull() & (files_in_redcap['non_nan_count'] > 0)]

