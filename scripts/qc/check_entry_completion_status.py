
# coding: utf-8

# Run this script as a standard Jupyter Notebook inside a production container (e.g. `pipeline-back`).

# In[ ]:


import pandas as pd
import re
import os
import redcap as rc
import numpy as np
from operator import itemgetter  # for extracting multiple keys from a dict

import sibispy
from sibispy import sibislogger as slog
import sys


# In[ ]:


# Setting pandas options for interactive displays
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 300)


# In[ ]:


session = sibispy.Session()
if not session.configure():
    sys.exit()

slog.init_log(None, None, 'QC_all: Completeness report', 'qc_all', None)
slog.startTimer1()


# In[ ]:


# Setting up API and specific constants for this run of QC
api = session.connect_server('data_entry', True)
primary_key = api.def_field

qc_event = '3y_visit_arm_1'
qc_arm = 1


# In[ ]:


def get_forms_for_qc(rc_api, event, arm=1):
    forms_events = rc_api.export_fem(format='df')
    if "form" in forms_events.columns:
        form_key = "form"
    else:
        form_key = "form_name"
    return (forms_events
            .query('unique_event_name == @event & arm_num == @arm', engine="python")
            .get(form_key).unique().tolist())
forms_for_qc = get_forms_for_qc(api, qc_event, qc_arm)


# At this point, it would be useful to:
# 
# 1. create a dictionary with each form as a dictionary key
# 2. iterate through the dictionary and for each key, export records as df and store that as the value in the dictionary
# 3. optionally, merge the data

# In[ ]:


forms_to_skip = ['biological_np', 'biological_mr', 'mr_session_report', 'mri_report']
[forms_for_qc.remove(form) for form in forms_to_skip]


# In[ ]:


forms_for_qc


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
    [df.to_csv("data_20180226/" + form + '.csv') for form, df in data_all.items()]


# In[ ]:


def merge_df_from_forms(form_names, data_all):
    """ Return a single pandas.DataFrame merged from data frames stored in a dict.
    
    `form_names` is assumed to be a list of keys, all of which exist in `data_all`.
    
    All data frames in the dictionary are assumed to be sharing their index."""
    selected_forms = itemgetter(*form_names)(data_all)
    return reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True), selected_forms)


# # Metadata / notes / dates
# A data frame to later left-join in order to check that there's no documented reason for the flagged concern.

# In[ ]:


all_meta = {form: data_all[form].filter(regex=r'_date$|_notes?$') for form in forms_for_qc}


# In[ ]:


meta_df = reduce(lambda x, y: pd.merge(x, y, left_index=True, right_index=True), 
                 all_meta.values())
notes_df = meta_df.filter(regex=r'_notes?$')
dates_df = meta_df.filter(regex=r'_date$')


# # Presence check: visit
# 
# Participants should either have a visit date or should be marked and explained for having missed it.

# In[ ]:


data_all['visit_date'].query('visit_date != visit_date & visit_ignore___yes != 1', engine="python")


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


#{form: df.columns.tolist() for form, df in data_all.items()}


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
np_iter = data_all['np_wrat4_word_reading_and_math_computation']    .query('np_wrat4_missing != 1 & np_wrat4_word_reading_and_math_computation_complete == 2', engine="python")    .filter(regex=r'^((?!missing|complete).)*$')    .stack(dropna=False)
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


def flag_potential_omissions_marked_complete(df):
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
    
    df_relevant = df.query(query_present_complete, engine="python")
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
np_flags = {form: flag_potential_omissions_marked_complete(data_all[form]) for form in np_forms}
np_flags


# In[ ]:


all_flags = {form: flag_potential_omissions_marked_complete(data_all[form]) for form in forms_for_qc}
all_flags


# In[ ]:


def checker(flags_dict, data_dict):
    def check_form(form_name):
        if form_name not in flags_dict or form_name not in data_dict:
            return None
        else:
            return pd.merge(notes_df, data_dict[form_name].loc[flags_dict[form_name]],
                            how='right', left_index=True, right_index=True)
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


# # Incomplete forms?
# 
# After talking to Devin, Ryan and Vanessa, I realized that the scope of this check was limited.
# 
# The previous check could best be characterized as "flagging records that were mistakenly labeled 'complete' when they were, in fact, missing information." This lets off the hook the records that were not marked missing and should have been.
# 
# But the interplay of `*_missing` and `*_complete` has slightly more complex rules / usage:
# 
# 1. If a form is marked missing, it should always be marked "complete". It might not, in practice, be marked that, but it should be.
# 2. If a form isn't marked missing, it might be marked either:
#     a. **incomplete** ("missing" in some data dictionaries, which is confusing): the data exists, but it hasn't been entered yet.
#     b. **unverified**: the data has been entered, but should be re-checked,
#     c. **complete**: the data as entered is currently assumed to be the complete record for that form.
#    
# So, essentially, there are five states a form can be in, and their failure modes are different:
# 
# 1. **Marked permanently missing**: should not have any data in it, and completion mark doesn't matter (but it _should_ be marked "complete"). Flag if:
#     * Has data, or
#     * Is not marked complete. (In theory, the script could auto-mark it complete, as there is no other resolution.)
# 2. **Not missing but incomplete**: site should enter data. **This is the default status of a form.** Flag if:
#     * The deadline for data collection has passed. (Data should either be filled in and form should be marked complete, or the form should be marked permanently missing and complete.)
# 3. **Not missing but unverified**: site should do the second part of double entry. Flag if:
#     * The deadline for data collection has passed.
#     * _Maybe?_ The data has been entered into the form more than n days ago.
# 4. **Not missing and complete**: site is done with the form (but might have overlooked something). Flag if:
#     * Participant is missing some responses that other participants have. (This is the original logic of this PR.)
# 5. **Not marked anything**: In theory, this shouldn't happen at all, so it should always be flagged.
# 
# The previous check doesn't bother with (1); it only addresses (4).
# 
# ## Checking for visit date?
# This is where it might make sense to check if the participant has _any_ data for the year.
# 
# Then again, maybe not? Global collection status may not matter to a form.
# 
# ## Checking for "should this visit be ignored?"
# In general, yes - e.g. exclusions at baseline will be marked that every year, and there's no way to tell just one form at a time.
# 
# (In the future, we might want to use specific exceptions for exclusion at baseline, but that doesn't change the case here.)

# ## Issue with checkboxes
# In some forms - biological NP, biological MR, maybe others? - checkboxes are used to solicit response. The default value that will be exported, **even if the form was not filled out**, is 0. Depending on whether the participant actually saw and filled out the form, the value `0` should be interpreted as either `0` (if seen) or `NaN` (if not seen).
# 
# This can be inferred from the presence of a date on _some_ forms, but not all. Here's a list of checkboxes that can be a problem:

# In[ ]:


forms_with_checkboxes = {
    'np_grooved_pegboard': ['np_gpeg_exclusion___dh', 'np_gpeg_exclusion___ndh'],
    'np_reyosterreith_complex_figure_files': ['np_reyo_ndh___yes'],
    'np_wais4_coding': ['np_wais4_rawscore_diff___correct'],
    'cnp_summary': [
             'cnp_instruments___testsessions',
             'cnp_instruments___cpf',
             'cnp_instruments___cpfd',
             'cnp_instruments___cpw',
             'cnp_instruments___cpwd',
             'cnp_instruments___medf36',
             'cnp_instruments___er40d',
             'cnp_instruments___mpract',
             'cnp_instruments___pcet',
             'cnp_instruments___pmat24a',
             'cnp_instruments___pvoc',
             'cnp_instruments___pvrt',
             'cnp_instruments___sfnb2',
             'cnp_instruments___shortvolt',
             'cnp_instruments___spcptnl',
             'cnp_instruments___svdelay',
    ],
}


# ## Implementation

# In[ ]:


def get_missing_and_complete_column_names(df):
    # some forms don't have it, some forms have it for multiple subsections
    cols_missing = get_items_matching_regex(r'missing$', df.columns)
    # all forms have it, some forms have it for multiple subsections
    cols_complete = get_items_matching_regex("complete$", df.columns)
    
    return cols_missing, cols_complete


# The good news is, there don't appear to be any data lost behind records labeled "missing". Of course, if REDCap wipes the data when the form is marked missing, that would be impossible.
# 
# False positives are due to checkboxes.

# In[ ]:


def flag_missing_with_data(df):
    # 1. is it marked missing
    # 2. does it have any fields that are filled out?
    cols_missing, cols_complete = get_missing_and_complete_column_names(df)
    
    if len(cols_missing) == 1:
        query_missing = "%s == 1" % cols_missing[0]
    else:
        return None
    
    df_relevant = df.query(query_missing, engine="python")
    if len(df_relevant) == 0:
        return None

    # Now, remove all complete / missing columns and stack
    df_relevant = df_relevant.filter(regex=r'^((?!missing|complete).)*$').        stack(dropna=True).count(level=0)
    return df_relevant[df_relevant > 0].index.tolist()

{form: flag_missing_with_data(data_all[form]) for form in forms_for_qc}


# In[ ]:


def flag_missing_not_marked_complete(df):
    # 1. is it flagged missing
    # 2. is it not flagged complete
    cols_missing, cols_complete = get_missing_and_complete_column_names(df)
    query_not_complete = " or ".join(["%s == 2" % col for col in cols_complete])
    
    if len(cols_missing) == 1:
        query_missing = "%s == 1" % cols_missing[0]
        query_not_complete = "(" + query_not_complete + ") and " + query_missing
    else:
        return None
 
    df_relevant = df.query(query_not_complete, engine="python")
    if len(df_relevant) == 0:
        return None
    return df_relevant.index.tolist()

    # Now, remove all complete / missing columns and stack
    df_relevant = df_relevant.filter(regex=r'^((?!missing|complete).)*$').        stack(dropna=False).count(level=0)
    return df_relevant[df_relevant == 0].index.tolist()
{form: flag_missing_not_marked_complete(data_all[form]) for form in forms_for_qc}


# This is where checkboxes are causing a lot of false _negatives_. Since the checkbox reports in as 0, it appears as though there's data.
# 
# This is also the most common status.

# In[ ]:


def flag_incomplete_without_data(df):
    # Equivalent of grey circle in REDCap.
    #
    # 1. is it marked incomplete
    # 2. is it not marked missing
    # 3. does it have any data
    
    # By default, forms are marked to receive more data, so this will return almost everything.
    # If they haven't received data by collection deadline, should be marked missing+complete
    cols_missing, cols_complete = get_missing_and_complete_column_names(df)
    query_incomplete = " or ".join(["%s == 0" % col for col in cols_complete])
    
    if len(cols_missing) == 1:
        query_present = "%s != 1" % cols_missing[0]
        query_incomplete = "(" + query_incomplete + ") and " + query_present
 
    df_relevant = df.query(query_incomplete, engine="python")
    if len(df_relevant) == 0:
        return None

    # Now, remove all complete / missing columns and stack
    df_relevant = df_relevant.filter(regex=r'^((?!missing|complete).)*$').        stack(dropna=False).count(level=0)
    return df_relevant[df_relevant == 0].index.tolist()

{form: flag_incomplete_without_data(data_all[form]) for form in forms_for_qc}


# The checkboxes are, again, causing a lot of false positives here: 

# In[ ]:


def flag_incomplete_with_data(df):
    # This is the equivalent of a red circle in REDCap.
    #
    # 1. is it marked incomplete
    # 2. is it not marked missing
    # 3. does it have any data
    #
    # Follow-up: Site should work to fill in data, or mark record as complete
    #  (or delete data if there was a mix-up)
    
    cols_missing, cols_complete = get_missing_and_complete_column_names(df)
    query_incomplete = " or ".join(["%s == 0" % col for col in cols_complete])
    
    if len(cols_missing) == 1:
        query_present = "%s != 1" % cols_missing[0]
        query_incomplete = "(" + query_incomplete + ") and " + query_present
 
    df_relevant = df.query(query_incomplete, engine="python")
    if len(df_relevant) == 0:
        return None

    # Now, remove all complete / missing columns and stack
    df_relevant = df_relevant.filter(regex=r'^((?!missing|complete).)*$').        stack(dropna=True).count(level=0)
    return df_relevant[df_relevant > 0].index.tolist()

{form: flag_incomplete_with_data(data_all[form]) for form in forms_for_qc}


# In[ ]:


def flag_unverified_forms(df):
    # These forms are marked to receive more data. 
    # It doesn't matter whether they're marked missing or not; they should be verified.
    
    cols_missing, cols_complete = get_missing_and_complete_column_names(df)
    query_unverified = " or ".join(["%s == 1" % col for col in cols_complete])
        
    df_relevant = df.query(query_unverified, engine="python")
    if len(df_relevant) == 0:
        return None
    return df_relevant.index.tolist()
unverified_flags = {form: flag_unverified_forms(data_all[form]) for form in forms_for_qc}
unverified_flags


# ## Divide flags up by site

# In[ ]:


def extract_flags_for_site(flags, site):  # Site is assumed to be a single character
    import re
    if flags:
        return [flag for flag in flags if re.match(r'^' + site, flag)]
    else:
        return None
def divide_flags_by_site(flags_by_form, sites = ['A', 'B', 'C', 'D', 'E']):
    by_site = dict.fromkeys(sites)
    for site in sites:
        by_site[site] = {form_name: extract_flags_for_site(form, site) for (form_name, form) in flags_by_form.items()}
    return by_site
unverified_by_site = divide_flags_by_site(unverified_flags)
unverified_by_site


# In[ ]:


event_mapping = {'baseline': 70,
                 '6-month': 71,
                 '1y': 72,
                 '18-month': 73,
                 '2y': 74,
                 '30-month': 75,
                 '3y': 76,
                 '42-month': 77,
                 '4y': 78}


# In[ ]:


def make_urls_for_ids_by_form(flags_by_form, event_id=76):
    root_url = 'https://ncanda.sri.com/redcap/redcap_v6.10.5/DataEntry/index.php'
    entry_link_schema = root_url + '?pid=20&id=%s&event_id=%d&page=%s'
    links = {}
    for form_name, form_flags in flags_by_form.iteritems():
        if form_flags:
            links[form_name] = {study_id: entry_link_schema % (study_id, event_id, form_name) for study_id in form_flags}
    return links


# ## Create templates

# In[ ]:


unverified_urls_by_site = {site: make_urls_for_ids_by_form(site_unverified) 
                           for site, site_unverified 
                           in unverified_by_site.items()}


# In[ ]:


for site, flags_by_form in unverified_urls_by_site.iteritems():
    print('# %s\n' % site)
    for form_name, flags_in_form in flags_by_form.iteritems():
        print('## %s\n' % form_name)
        for study_id, url in flags_in_form.iteritems():
            print('* [%s](%s)' % (study_id, url))
    

