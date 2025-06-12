"""
Tools for working with raw and processed LimeSurvey forms in NCANDA pipeline

Primarily used by find_limesurvey_status.

FIXME:
- Form number is not sufficient for identifying whether LSSAGA is Youth or Parent -- necessary to consult `_typeintertranslate`
"""
from builtins import zip
from builtins import str
import pandas as pd
import numpy as np
from fnmatch import fnmatch
from itertools import chain

def limesurvey_number_to_name(ls_number, lookup_df=None, short=True,
                              raise_error=True):
    if lookup_df is None:
        lookup_df = get_ncanda_form_lookup(as_dataframe=True)
    try:
        return lookup_df.loc[str(ls_number),
                             'short_name' if short else 'long_name']
    except KeyError:
        if raise_error:
            raise
        else:
            return np.nan


def limesurvey_name_to_number(ls_name, lookup_df=None):
    if lookup_df is None:
        lookup_df = (get_ncanda_form_lookup(as_dataframe=True)
                     .reset_index()
                     # .set_index('short_name' if short else 'long_name'))
                     .set_index(['short_name', 'long_name']))

    # MultiIndex here should guarantee that no matter whether the form name
    # passed is short or long, it will successfully look up the corresponding
    # form number.
    #
    # sortlevel is necessary because of a lexdepth issue on pandas 0.14
    return lookup_df.sortlevel(0, axis=0).loc[ls_name, 'ls_number'].tolist()

def limesurvey_name_short_to_long(ls_name, lookup_df=None):
    if lookup_df is None:
        lookup_df = get_ncanda_form_lookup(as_dataframe=True)
    lookup_dict = dict(list(zip(lookup_df['short_name'], lookup_df['long_name'])))
    return lookup_dict.get(ls_name)

def limesurvey_name_glob_to_names(ls_glob, lookup_df=None):
    if lookup_df is None:
        lookup_df = (get_ncanda_form_lookup(as_dataframe=True))
    short_names = lookup_df['short_name'].tolist()
    # fnmatch is the function internally used by glob
    return list(set([x for x in short_names if fnmatch(x, ls_glob)]))


def limesurvey_name_glob_to_numbers(ls_glob, lookup_df=None):
    # form_names = limesurvey_name_glob_to_names(ls_glob, lookup_df)
    # FIXME: lookup_df is presumed to be indexed in a particular way, but that
    #   particular way is different for limesurvey_name_to_number and
    #   limesurvey_number_to_name, so we cannot pass it to both
    form_names = limesurvey_name_glob_to_names(ls_glob)
    # using itertools.chain because limesurvey_name_to_number returns a list
    return list(set(chain(*[limesurvey_name_to_number(x)
                            for x in form_names])))


def get_within_file_info(fname, is_lssaga=False):
    df = pd.read_csv(fname, dtype=object)
    main_id = df.filter(regex="subjid$")
    # TODO: Process into a single array of IDs that are different from main
    aux_ids = df.filter(regex="subjid.$").dropna()
    main_date = df.filter(regex="[cC]ompleted$|^[dD]ate_").dropna()
    # survey_date_fields = [ 'completed', 'date_started', 'date_last_action', 'date_interview']
    if is_lssaga:
        lssaga_type = pd.DataFrame({
            'lssaga_type': [get_lssaga_type(df, raise_error=False)]
        })
    else:
        lssaga_type = pd.DataFrame()
    return pd.concat([main_date, main_id, aux_ids, lssaga_type], axis=1)


def get_lssaga_type(df, raise_error=False):
    try:
        typeinter = str(df['typeinter'].iloc[0])
    except KeyError:
        if raise_error:
            raise
        else:
            return ''

    if typeinter == '0':
        lssaga_type = "_parent"
    elif typeinter == '1':
        lssaga_type = "_youth"
    elif raise_error:
        raise ValueError("typeinter is %s, expected '0' or '1'" % typeinter)
    else:
        lssaga_type = ''
    return lssaga_type


def get_import_url(df,
                   base_url="https://ncanda.sri.com/redcap/redcap_v8.4.0/"
                            "DataEntry/index.php?pid=6&event_id=21"):
    if 'proc_form' not in df.columns:
        # Assume it's in index
        df['proc_form'] = df.index.get_level_values('form')
    df['form_long'] = df['proc_form'].apply(limesurvey_name_short_to_long)
    df['url'] = (base_url + "&id=" + df['import_id']
                 + '&page=' + df['form_long'])
    # df.drop(columns=['form_long', 'import_id'], inplace=True)
    return df


def get_completion_status_in_redcap(redcap, forms=None, subjects=None):
    """
    redcap - API handle provided by PyCap / sibispy.Session
    """
    if not forms:
        forms = (redcap.export_metadata(format_type='df')
                 .reset_index().form_name.unique()
                 .tolist())
    fields = [x + "_complete" for x in forms]

    status_df = redcap.export_records(fields=fields, records=subjects,
                                      format_type='df')
    status_df = status_df.stack()
    status_df.name = 'status'
    status_df.index.names = ['record_id', 'form']
    status_df = status_df.to_frame().reset_index()
    status_df.loc[:, 'form'] = status_df.form.str.replace('_complete$', '')
    return status_df
 

def get_completion_status_for_pipe(df, redcap):
    forms = df['form_long'].dropna().unique().tolist()
    subjects = df['import_id'].dropna().unique().tolist()
    status = get_completion_status_in_redcap(redcap, forms=forms,
                                             subjects=subjects)
    df_with_status = pd.merge(df, status,
                              how='left',
                              left_on=['import_id', 'form_long'],
                              right_on=['record_id', 'form'])
    return df_with_status


def get_ncanda_form_lookup(as_dataframe=True):
    # Taken from ncanda-data-integration/scripts/import/laptops/lime2csv
    # FIXME: Form number is not sufficient for identifying whether LSSAGA is
    #   Youth or Parent -- necessary to consult `_typeintertranslate`
    lookup_dict = {
        # Baseline surveys:
        '11584': ('youthreport1', 'youth_report_1'),
        '12471': ('youthreport2', 'youth_report_2'),
        '31627': ('parentreport', 'parent_report'),
        # Original MRI Report
        '32869': ('mrireport', 'mri_report'),
        # Improved MRI Report with Y/N skip-outs
        '29516': ('mrireport', 'mri_report'),
        '75894': ('plus', 'participant_last_use_summary'),
        # Six-month survey:
        '54587': ('myy', 'midyear_youth_interview'),
        # One year follow-up surveys:
        '13947': ('youthreport1', 'youth_report_1'),
        '72223': ('youthreport1b', 'youth_report_1b'),
        '92874': ('youthreport2', 'youth_report_2'),
        '21598': ('parentreport', 'parent_report'),
        # One year follow-up SSAGA (each part has an old and a new version;
        # new version has some modules hidden from interviewer, but should
        # otherwise be the same as the old):
        # FIXME: Should remove _youth / _parent, because that's not how these
        #   forms work -- which type they are is judged from the content
        '14134': ('lssaga1_parent', 'limesurvey_ssaga_part_1_parent'),
        '82982': ('lssaga1_youth', 'limesurvey_ssaga_part_1_youth'),
        '72261': ('lssaga1_youth', 'limesurvey_ssaga_part_1_youth'),  # modified on YR4
        '81475': ('lssaga2_parent', 'limesurvey_ssaga_part_2_parent'),
        '37237': ('lssaga2_youth', 'limesurvey_ssaga_part_2_youth'),
        '91768': ('lssaga3_parent', 'limesurvey_ssaga_part_3_parent'),
        '29231': ('lssaga3_youth', 'limesurvey_ssaga_part_3_youth'),
        '12396': ('lssaga4_parent', 'limesurvey_ssaga_part_4_parent'),
        '56922': ('lssaga4_youth', 'limesurvey_ssaga_part_4_youth'),
        # Sleep surveys:
        '29361': ('sleepeve', 'sleep_study_evening_questionnaire'),
        '82312': ('sleepeve', 'sleep_study_evening_questionnaire'),
        '96417': ('sleepmor', 'sleep_study_morning_questionnaire'),
        '88371': ('sleeppre', 'sleep_study_presleep_questionnaire'),
        '34495': ('sleeppre', 'sleep_study_presleep_questionnaire'),
        # Recovery Forms
        '67375': ('recq', 'recovery_questionnaire'),
        # Longitudinal follow-up surveys: (mostly from YR2 to YR3)
        '17895': ('youthreport1', 'youth_report_1'),  # Improved YR1
        '11772': ('youthreport1b', 'youth_report_1b'),  # Improved YR1b
        '25126': ('youthreport2', 'youth_report_2'),  # Improved YR2
        '27974': ('parentreport', 'parent_report'),  # Improved Parent Report
        '41833': ('mrireport', 'mri_report'),  # Improved MRI Report
        '97714': ('plus', 'participant_last_use_summary'),  # Improved PLUS

        # Longitudinal six-month survey: (should not need to be changed!)
        '79454': ('myy', 'midyear_youth_interview'),
    }
    if as_dataframe:
        lookup_df = pd.DataFrame.from_dict(lookup_dict, orient='index')
        lookup_df.index.name = 'ls_number'
        new_cols = ['short_name', 'long_name', 'latest']
        lookup_df.columns = new_cols[0:len(lookup_df.columns)]
        return lookup_df
    else:
        return lookup_dict
