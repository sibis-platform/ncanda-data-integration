
# coding: utf-8

# # Detecting unuploaded forms based on the company they keep
# 
# Some forms are always completed together. If one is uploaded and the others are not, then we should start looking for the reason why and either locate the form or mark it missing.

# In[1]:


import pandas as pd
import numpy as np
import sibispy
from sibispy import sibislogger as slog
import sys


# In[2]:


pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)


# In[3]:


session = sibispy.Session()
if not session.configure():
    sys.exit()

slog.init_log(None, None, 
              'QC: Check that logical groupings of forms are uploaded', 
              'check_form_groups', None)
slog.startTimer1()

# Setting specific constants for this run of QC
api = session.connect_server('data_entry', True)
primary_key = api.def_field


# In[4]:


meta = api.export_metadata(format='df')


# In[8]:


def get_items_matching_regex(regex, haystack):
    import re
    return [x for x in haystack if re.search(regex, x)]


# To be considered as "having content", the form has to pass any of the three tests:
# 
# 1. Is it marked missing? If yes, then it has known content.
# 2. Is it marked complete? If yes, then it has known content.
# 3. Does it have non-NaN answers? If yes, then it has known content.
# 
# In future iterations, it might not be unreasonable to stop considering the completion status -- if there is no content, then the record should be marked missing, not just complete.

# In[60]:


def form_has_content(row):
    """ If the form is knowledgeably not empty (e.g. marked missing or 
    marked complete) or it has content in it, it is considered to have content. """
    try:
        columns = row.columns.tolist()
    except:
        columns = row.index.tolist()
    cols_complete = get_items_matching_regex("complete$", columns)
    cols_missing  = get_items_matching_regex("missing$", columns)
    cols_checklist = get_items_matching_regex("___", columns)
    
    if cols_missing:
        missing = (row[cols_missing] == 1).any()
    else:
        missing = None
    
    if cols_complete:
        complete = (row[cols_complete] in [2]).any()
    else:
        complete = False
    
    non_nan_items = row.drop(cols_complete + cols_missing + cols_checklist).notnull().any()
    
    return missing | complete | non_nan_items


# These are the forms that should co-occur. If they don't, then something has gone wrong.

# In[88]:


form_groups = {
    'sleep': ['sleep_study_evening_questionnaire',
              'sleep_study_presleep_questionnaire',
              'sleep_study_morning_questionnaire'],
    'mri': ['mr_session_report',
            'mri_report'],
    'deldisc': ['delayed_discounting_1000',
                'delayed_discounting_100'],
    'youth_report': ['youth_report_1',
                     'youth_report_1b',
                     'youth_report_2']
}


# Currently, the records get exported separately for each form group. Depending on future benchmarking, it might make sense to just get all the records and then scrape out the columns of interest.

# In[116]:


results = pd.DataFrame()
results_detailed = pd.DataFrame()
for group_name, form_group in list(form_groups.items()):
    data = api.export_records(fields=[api.def_field], forms=form_group, format="df")
    form_group_fields = [meta.loc[meta['form_name'] == form].index.tolist()
                         for form in form_group]
    per_form_results = [data.loc[:, form_fields].apply(form_has_content, axis=1) for form_fields in form_group_fields]
    per_form_results = pd.concat(per_form_results, axis=1)
    per_form_results.columns = form_group
    group_results = (per_form_results
                     .apply(lambda row: row.any() and not row.all(), axis=1))
    group_results.name = group_name
    results = pd.concat([results, group_results], axis=1)
    results_detailed = pd.concat([results_detailed, group_results, per_form_results], axis=1)


# ## Any participant/event combinations where one form is missing

# In[125]:


results.loc[results.apply(pd.Series.any, axis=1)]

