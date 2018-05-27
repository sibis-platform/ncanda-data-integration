import pandas as pd
import argparse
import sys
from aseba_utils import process_demographics_file, get_year_set
import aseba_form
import sibispy
from sibispy import sibislogger as slog

parser = argparse.ArgumentParser(
    description="Export fields on selected form to ADM before ASEBA scoring.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('-f', '--form',
                    choices=["asr", "ysr", "cbc"],
                    help="ASEBA form to extract the raw values for",
                    # nargs="+",
                    required=True)
parser.add_argument('-o', '--output', help="CSV file to write output to.",
                    action="store", default=sys.stdout)
parser.add_argument('-y', '--year', help="Last year to include (0 = baseline)",
                    action="store", default=0, type=int)
parser.add_argument('--demographics-file',
                    help="File with subjects for release",
                    action="store", default=None)
parser.add_argument('-t', '--threshold',
                    help=("Number of non-empty responses a participant must "
                          "have to be included."),
                    default=100, type=int)
args = parser.parse_args()

selected_events = get_year_set(args.year)

session = sibispy.Session()
if not session.configure():
    sys.exit()

slog.init_log(None, None, 'ASEBA: Initial pre-scoring data retrieval', 'aseba_prep', None)
slog.startTimer1()

project_entry = session.connect_server('data_entry', True)

## 1. Extract general info
additional_columns = ['study_id', 'redcap_event_name', 'dob', 'age']
# note that we don't actually need DOB (since age is calculated for each visit)
general_df = project_entry.export_records(fields=additional_columns,
                                          events=selected_events,
                                          format='df')

## 2. Filter out records based on a demographics file from a data release
if args.demographics_file:
    demog = process_demographics_file(args.demographics_file)
    general_df = pd.merge(general_df, demog,
                          left_index=True, right_index=True,
                          how='right')

## 3. Round age and remove records with uncalculated age
general_df['age'] = general_df['age'].round(decimals=0)
general_df = general_df.dropna(subset=['age'])
general_df['age'] = general_df['age'].astype(int)

if args.form == "asr":
    form_specifics = aseba_form.FormASR()
if args.form == "ysr":
    form_specifics = aseba_form.FormYSR()
if args.form == "cbc":
    form_specifics = aseba_form.FormCBC()

## 4. Extract form-specific info
aseba_df = project_entry.export_records(fields=['study_id'],
                                        events=selected_events,
                                        forms=[form_specifics.form],
                                        format='df')
# filter columns so that they start with youthreport1_asr_section
# only keep rows that have at least 100 responses
aseba_df_answers = (aseba_df.filter(regex=form_specifics.form_field_regex)
                    .dropna(axis=0, how='any', thresh=args.threshold)
                    .fillna(value=9))

## 5. Shrink into a single column
aseba_df_answers['bpitems'] = (aseba_df_answers
                             .iloc[:, 0:(len(aseba_df_answers.columns))]
                             .astype(int)
                             .astype(str)
                             .apply(lambda x: "'" + ''.join(x), axis=1))

aseba_df_bpitems = aseba_df_answers.loc[:, ['bpitems']]

# with NaN-containing answers filtered out, grab age and XNAT SID for the
# surviving records
output_df = pd.merge(general_df, aseba_df_bpitems,
                     left_index=True, right_index=True,
                     how='inner')

# Using the fact that pandas will automatically create an index as
# range(nrows), we obtain subjectno instead of creating it ourselves.
# - maybe it would be more pythonic to just assign range(n) to the column.
output_df = output_df.reset_index()
output_df.index.rename('subjectno', inplace=True)
output_df = output_df.reset_index()  # get subjectno as a column

# Assign the constant values required by ADM
# In pandas 0.16, output_df = output_df.assign(**form_specifics.constant_fields)
for k, v in form_specifics.constant_fields.items():
    output_df[k] = v

# Extract gender from study ID
output_df['gender'] = output_df['study_id'].str.extract(r'([MF])-[0-9]$')  # , expand=False)

# Rename columns to be reused
output_df = output_df.rename(columns={'study_id': 'firstname',
                                      'mri_xnat_sid': 'middlename',
                                      'redcap_event_name': 'lastname'})

# Rearrange existing columns and fill the non-existent one with NaNs
adm_headers=["admver", "datatype", "subjectno", "id", "firstname",
             "middlename", "lastname", "othername", "gender", "dob",
             "ethniccode", "formver", "dataver", "formno", "formid", "type",
             "enterdate", "dfo", "age", "agemonths", "educcode", "fobcode",
             "fobgender", "fparentses", "fsubjses", "fspouseses", "agencycode",
             "clincode", "bpitems", "compitems", "afitems", "otheritems",
             "experience", "scafitems", "facilityco", "numchild", "hours",
             "months", "schoolname", "schoolcode", "tobacco", "drunk", "drugs",
             "drinks", "ctimecode", "ctypecode", "early", "weeksearly",
             "weight", "lb_gram", "ounces", "infections", "nonenglish",
             "slowtalk", "worried", "spontan", "combines", "mlp", "words162",
             "words310", "otherwords", "totwords", "origin", "fudefcode1",
             "fudefcode2", "sudefcode1", "interviewr", "rater", "fstatus",
             "usertext", "sparentses", "ssubjses", "cas", "casfsscr", "das",
             "dasgcascr", "kabc", "kabcmpcscr", "sb5", "sb5fsiqscr", "wj3cog",
             "wj3cogscr", "wais3", "wais3scr", "wisc4", "wisc4scr", "wppsi3",
             "wppsi3scr", "other1test", "othtst1scr", "other2test",
             "othtst2scr", "other3test", "othtst3scr", "other1name",
             "other2name", "other3name", "obstime", "rptgrd", "medic",
             "medicdesc", "dsmcrit", "dsmcode1", "dsmdiag1", "dsmcode2",
             "dsmdiag2", "dsmcode3", "dsmdiag3", "dsmcode4", "dsmdiag4",
             "dsmcode5", "dsmdiag5", "dsmcode6", "dsmdiag6", "illness",
             "illdesc", "speced", "sped1", "sped2", "sped3", "sped4", "sped5",
             "sped6", "sped7", "sped8", "sped9", "sped10", "sped10a",
             "sped10b", "sped10c", "admcatlg", "society", "cethnic", "ceduc",
             "cfob", "cagency", "cclin", "cintervr", "crater", "cfacilit",
             "ctime", "ctype", "cschool", "cfudef1", "cfudef2", "csudef1"]
output_df = output_df.reindex(columns=adm_headers)
output_df.to_csv(args.output, index=False)
