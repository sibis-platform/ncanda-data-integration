import pandas as pd

def process_demographics_file(filename):
    df = pd.read_csv(filename)
    df = df[df['visit'] == 'baseline']
    df = df[['subject', 'participant_id']]
    df = df.rename(columns={'participant_id': 'study_id',
			    'subject': 'mri_xnat_sid'})
    df.set_index('study_id', inplace=True)
    return df

def get_year_set(year_int):
    events = ["baseline"]
    events.extend([str(i) + "y" for i in xrange(1, 10)])
    events = [e + "_visit_arm_1" for e in events]
    return events[0:(year_int + 1)]
