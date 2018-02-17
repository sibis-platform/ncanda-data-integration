
# coding: utf-8

# In[ ]:

import pandas as pd
import redcap as rc
import re
import os
from operator import itemgetter  # for extracting multiple keys from a dict


# In[ ]:

# Setting pandas options for interactive displays
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 300)


# In[ ]:

# Setting specific constants for this run of QC
api_url = 'https://ncanda.sri.com/redcap/api/'
api_key = os.environ['REDCAP_API_KEY']
api = rc.Project(api_url, api_key)
primary_key = api.def_field

qc_event = '3y_visit_arm_1'
qc_arm = 1


# In[ ]:

def get_forms_for_qc(rc_api, event, arm=1):
    forms_events = rc_api.export_fem(format='df')
    return forms_events.        query('unique_event_name == @event & arm_num == @arm').        form_name.unique().tolist()
forms_for_qc = get_forms_for_qc(api, qc_event, qc_arm)


# At this point, it would be useful to:
# 
# 1. create a dictionary with each form as a dictionary key
# 2. iterate through the dictionary and for each key, export records as df and store that as the value in the dictionary
# 3. optionally, merge the data

# In[ ]:

def get_data_for_event(rc_api, event, forms=None, arm=1):
    if forms is None:
        forms = get_forms_for_qc(rc_api, event, arm)
    
    return dict((form_name, 
                 rc_api.export_records(format='df',
                                       fields=[rc_api.def_field], 
                                       events=[event],
                                       forms=[form_name]).\
                 reset_index(level='redcap_event_name', 
                             drop=True)) 
                for form_name in forms)
data_all = get_data_for_event(api, qc_event)


# In[ ]:

# Save the intermediate product if needed
save_to_csv = False
if save_to_csv:
    [df.to_csv("data_20180215/" + form + '.csv') for form, df in data_all.items()]


# In[ ]:

def merge_df_from_forms(form_names, data_all):
    """ Return a single pandas.DataFrame merged from data frames stored in a dict.
    
    `form_names` is assumed to be a list of keys, all of which exist in `data_all`.
    
    All data frames in the dictionary are assumed to be sharing their index."""
    selected_forms = itemgetter(*form_names)(data_all)
    return reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True), selected_forms)


# # Presence check: visit
# 
# Participants should either have a visit date or should be marked and explained for having missed it.

# In[ ]:

data_all['visit_date'].query('visit_date != visit_date & visit_ignore___yes != 1')


# # Quality / presence check: MRI

# In[ ]:

# 1. Do you have a visit date?
def has_visit(all_forms_data):
    return all_forms_data['visit_date']['visit_date'].notnull()


# In[ ]:

def has_missing_scans(all_forms_data):
    # 2. Do you have any missing scan dates?
    missing_scan_date = all_forms_data['mr_session_report'].        filter(regex=r'_date$').isnull().any(axis=1)
    # 3. Are you marked as not missing?
    not_marked_missing = all_forms_data['mr_session_report']['mri_missing'].isnull()
    return missing_scan_date & not_marked_missing


# In[ ]:

def show_mr_flags(all_forms_data):
    flagged_subset = all_forms_data['mr_session_report'][has_visit(data_all) & 
                                                         has_missing_scans(data_all)]
    return pd.merge(flagged_subset, 
                    data_all['visit_date'], 
                    how='left', 
                    left_index=True, right_index=True)


# In[ ]:

show_mr_flags(data_all).filter(regex=r'^mri_xnat|_date$|missing$|visit_notes|mri_notes')


# After this, the follow-up would be to:
# 
# 1. Check the notes of this final subset to see if scan absence is indicated. If not, contact the sites.
# 2. Ask sites to either (1) upload the scans or (2) update `mri_missing` (if _all_ scans are missing) or `mri_notes` (if _some_ scans are missing)

# # Quality check: NPs

# Now, the general quality check follows this logic:
# 
# 1. Is there a visit date?
# 2. If yes, are the NPs filled out? / How many NPs in each form are filled out?

# In[ ]:

np_keys = filter(lambda x: x.startswith('np'), data_all.keys())
np_keys = ['visit_date'] + np_keys


# In[ ]:

np_data = itemgetter(*np_keys)(data_all)


# In[ ]:

# merging on indices which are guaranteed to be shared
np_data_all = reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True), np_data)


# With most forms, we might be interested in the number of non-answers. After all, there's a lot of fields that patients fill out:

# In[ ]:

{form: df.columns.tolist() for form, df in data_all.items()}


# ...so we'll re-shape them from wide to long and count up the absences.
# 
# ## WRAT4
# 
# Trying the approach out on WRAT4, we do the following:
# 
# 1. check that the record is not missing (should also check presence of visit date - or maybe subjects without visit date should have been purged at an earlier stage?)
# 2. check that the record is completed (=2)
# 3. stack the substantive fields and flag subjects with fewer than max responses
# 
# Step 3 ensures that we don't flag forms nobody has answered. It does rely on the intuition that if someone has answered a field, everyone should. It would fail for casees where many people have the same *number* of non-answers, but each in different fields. It certainly fails in more complex forms where some a field's necessity is conditional on previous responses.

# In[ ]:

# ^((?!missing|complete).)*$ is negative lookahead matching everything except the string 'missing'
np_iter = data_all['np_wrat4_word_reading_and_math_computation']    .query('np_wrat4_missing != 1 & np_wrat4_word_reading_and_math_computation_complete == 2')    .filter(regex=r'^((?!missing|complete).)*$')    .stack(dropna=False)
    #set_index(['np_wrat4_missing', 'np_wrat4_missing_why', 'np_wrat4_missing_why_other'], append=True).\


# In[ ]:

counts = np_iter.count(level=0)
incomplete = counts < counts.max()
# note: I can't use this to index the original frame because this Series is shorter; 
#       I can't use .index because all the participants are still in it, regardless
#       of truth or falsity of `incomplete`. There should be a more elegant way to do this.
#
# Maybe a variation on dfd.loc[dfd.index[[0, 2]]]?
counts_incomplete = counts[incomplete] 


# In[ ]:

counts_incomplete


# In[ ]:

np_iter.loc[counts_incomplete.index.tolist()].isnull()


# ## Wider subset of NP reports

# In[ ]:

np_forms = forms_for_qc[9:15] # could also filter with a regex


# ### ~~Approach 1: Merge all items and evaluate them together~~
# This could work but might not have the level of granularity that is useful to a human.

# In[ ]:

#np_data = merge_df_from_forms(['visit_date'] + np_data, data_all)


# ### Approach 2: Evaluate each form separately, bring together the results
# 
# Using the same drill as for WRAT4. Of course, one issue is that some forms really contain multiple subforms that are not  easily separable:

# In[ ]:

def get_items_containing(needle, haystack):
    return [elt for elt in haystack if needle in elt]
def get_items_matching_regex(regex, haystack):
    return filter(lambda x: re.search(regex, x), haystack)


# In[ ]:

{form: get_items_matching_regex(r"complete$|missing$", df.columns) for form, df in data_all.items()}


# You can see the "multiple" subforms e.g. in form `clinical`, which has multiple completion variables (but no missingness variables - which is a separate problem).
# 
# As for why they're not easily separable, consider that the naming convention isn't stable: in `biological_mr`, the completion variable is `biological_mr_complete`, but the missingness variable is `bio_mr_complete`.
# 
# Since there's only 35 forms, and only a bunch don't follow rules, creating custom rules for each in order to be able to do the broader QC check on all is not impossible, merely inelegant.

# In[ ]:

def flag_incomplete_forms(df):
    # some forms don't have it, some forms have it for multiple subsections
    cols_missing = get_items_matching_regex(r'missing$', df.columns)
    # all forms have it, some forms have it for multiple subsections
    cols_complete = get_items_matching_regex("complete$", df.columns)
    
    if len(cols_complete) > 1: # TODO: In the future, don't give up
        return "Too many complete fields"
    
    # Constructing the query
    # 
    # We want to flag a participant for whom:
    # 1. one or more subsections were *not* marked missing
    # 2. one or more subsections of the record were marked complete
    # 
    # The issue making this difficult is that there isn't necessarily a
    # one-to-one matching between the presence of missingness cols and 
    # the presence of completeness cols.
    #
    # In general, though, if at least one section is not marked missing,
    # and if at least one section is marked complete, the subject is game.
    #
    # (Future direction: plug-in lambdas for each form?)
    query_present_complete = "%s == 2" % cols_complete[0]
    if len(cols_missing) == 1:
        query_present = "%s != 1" % cols_missing[0]
        query_present_complete = query_present_complete + " and " + query_present
    
    df_relevant = df.query(query_present_complete)
    if len(df_relevant) == 0:
        return "No participants filled out the form"
    
    # Now, remove all complete / missing columns and stack
    df_relevant = df_relevant.filter(regex=r'^((?!missing|complete).)*$').        stack(dropna=False)
    counts = df_relevant.count(level=0)
    incomplete = counts < counts.max()
    counts_incomplete = counts[incomplete]
    
    return counts_incomplete.index.tolist()


# In[ ]:

# map(flag_incomplete_forms, np_data)
np_flags = {form: flag_incomplete_forms(data_all[form]) for form in np_forms}
np_flags


# In[ ]:

all_flags = {form: flag_incomplete_forms(data_all[form]) for form in forms_for_qc}
all_flags


# In[ ]:

def checker(flags_dict, data_dict):
    def check_form(form_name):
        if form_name not in flags_dict or form_name not in data_dict:
            return None
        else:
            return data_dict[form_name].loc[flags_dict[form_name]]
    return check_form
check_form = checker(all_flags, data_all)


# In[ ]:

check_form('brief')


# In[ ]:

check_form('stroop')


# In[ ]:

check_form('np_wrat4_word_reading_and_math_computation')


# In[ ]:

check_form('np_reyosterrieth_complex_figure')


# In[ ]:

check_form('np_reyosterrieth_complex_figure_files')


# In[ ]:

check_form('np_modified_greglygraybiel_test_of_ataxia')


# In[ ]:

check_form('parent_report')


# In[ ]:

check_form('participant_last_use_summary')


# In[ ]:

# flagged_data = {form: data_all[form].loc[flags] for form, flags in all_flags.values() if isinstance(flags, list)}

