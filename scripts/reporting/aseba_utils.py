import pandas as pd
import re

def process_demographics_file(filename):
    df = pd.read_csv(filename)
    # df = df[df['visit'] == 'baseline']
    df = df[['subject', 'arm', 'visit', 'participant_id', 'visit_age', 'sex']]
    df['mri_xnat_sid'] = df['subject']
    df = df.rename(columns={'participant_id': 'study_id',
                            'visit_age': 'age'})
    df.set_index(['subject', 'arm', 'visit'], inplace=True)
    return df


def get_year_set(year_int):
    events = ["baseline"]
    events.extend([str(i) + "y" for i in xrange(1, 10)])
    events = [e + "_visit_arm_1" for e in events]
    return events[0:(year_int + 1)]


def load_redcap_summary(file, index=True):
    index_col = ['subject', 'arm', 'visit'] if index else None
    df = pd.read_csv(file, index_col=index_col, dtype=object, low_memory=False)
    return df


def load_redcap_summaries(files):
    return pd.concat([load_redcap_summary(x) for x in files], axis=1)


def get_id_lookup_from_demographics_file(demographics_df):
    return (demographics_df
            .reset_index()
            .set_index('study_id')
            .to_dict()
            .get('mri_xnat_sid'))


def api_result_to_release_format(api_df, id_lookup_dict, verbose=False):
    """
    Reindex a PyCAP API result to an NCANDA release format.

    REDCap API, when used with PyCAP, returns results as a DataFrame indexed by
    NCANDA ID (study_id - X-00000-Y-0) and combined event + arm
    (redcap_event_name)

    On the other hand, release files are typically indexed by XNAT ID
    (NCANDA_S0?????; mri_xnat_id in Redcap).
    """

    df = api_df.copy(deep=True)
    df.reset_index(inplace=True)
    if id_lookup_dict:
        df['subject'] = df['study_id'].map(id_lookup_dict)
    elif 'mri_xnat_sid' in df.columns:
        df['subject'] = df['mri_xnat_sid']
    else:
        raise IndexError("You must supply id_lookup_dict, or api_df has to "
                         "have the mri_xnat_sid column")
    nan_idx = df['subject'].isnull()
    if verbose:
        study_id_nans = df.loc[nan_idx, 'study_id'].tolist()
        print ("Dropping study IDs without corresponding NCANDA SID: " +
               ", ".join(study_id_nans))
    df = df[~nan_idx]
    df[['visit', 'arm']] = (df['redcap_event_name']
                            .str.extract(r'^(\w+)_(arm_\d+)$'))

    def clean_up_event_string(event):
        # NOTE: Only accounts for full Arm 1 events
        match = re.search(r'^(baseline|\dy)', event)
        if not match:
            return event
        elif re.match('^\d', match.group(1)):
            return "followup_" + match.group(1)
        else:
            return match.group(1)

    df['visit'] = df['visit'].map(clean_up_event_string)

    def clean_up_arm_string(arm):
        arm_dict = {'arm_1': 'standard',
                    'arm_2': 'recovery',
                    'arm_3': 'sleep',
                    'arm_4': 'maltreated'}
        if arm not in arm_dict:
            return arm
        else:
            return arm_dict[arm]

    df['arm'] = df['arm'].map(clean_up_arm_string)

    return df.set_index(['subject', 'arm', 'visit'])
