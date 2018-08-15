#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Transform Redcap Youth/Parent Report data into an ASEBA ADM-compatible format.

`--demographics-file` is used for both subject exclusion and NCANDA SID lookup.

To use release data, you could invoke the command like so:

```bash
RELEASE_FOLDER=/fs/ncanda-share/releases/consortium/followup_3y/NCANDA_RELEASE_3Y_REDCAP_MEASUREMENTS_V02/summaries/redcap
OUT_FOLDER=/tmp
for form in asr ysr cbc; do
  ./aseba_prep.py --form $form \
    --demographics-file ${RELEASE_FOLDER}/demographics.csv \
    --input ${RELEASE_FOLDER}/youthreport*.csv \
            ${RELEASE_FOLDER}/parentreport.csv \
    --output ${OUT_FOLDER}/${form}_prepped.csv
done
```

To pull the data from the API:

```bash
for form in asr ysr cbc; do
  ./aseba_prep.py -f $form -y 3 \
    --demographics-file ${RELEASE_FOLDER}/demographics.csv
    --output ${OUT_FOLDER}/${form}_prepped.csv
done
```

"""
import pandas as pd
import argparse
import sys
from aseba_utils import (process_demographics_file,
                         get_year_set,
                         api_result_to_release_format,
                         get_id_lookup_from_demographics_file,
                         load_redcap_summaries)
from aseba_form import get_aseba_form
import sibispy
from sibispy import sibislogger as slog

parser = argparse.ArgumentParser(
    description="Export fields on selected form to ADM before ASEBA scoring.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('-f', '--form',
                    choices=["asr", "ysr", "cbc"],
                    help="ASEBA form to extract the raw values for",
                    required=True)
parser.add_argument('-i', '--input',
                    nargs="*",
                    metavar="<REDCAP_SUMMARY_FILES>",
                    help=("Redcap files from summaries/ folder of NCANDA "
                          "releases. If none are provided, REDCap API will be "
                          "used to draw up-to-date data. If any are provided, "
                          "REDCap API will not be used."))
parser.add_argument('-o', '--output', help="CSV file to write output to.",
                    action="store", default=sys.stdout)
parser.add_argument('-y', '--year',
                    help="Last year to include (0 = baseline). Note that this"
                         "filter isn't applied to files provided via --input.",
                    action="store", default=0, type=int)
parser.add_argument('--demographics-file',
                    help="File with subjects for release",
                    action="store", default=None)
parser.add_argument('-t', '--threshold',
                    help=("Number of non-empty responses a participant must "
                          "have to be included."),
                    default=100, type=int)
parser.add_argument('-v', '--verbose',
                    help="Print script operations to stdout",
                    action="store_true",
                    default=False)
args = parser.parse_args()

selected_events = get_year_set(args.year)

session = sibispy.Session()
if not session.configure():
    sys.exit()

slog.init_log(None, None, 'ASEBA: Initial pre-scoring data retrieval',
              'aseba_prep', None)
slog.startTimer1()

project_entry = session.connect_server('data_entry', True)

## 1. Extract general info
if not args.demographics_file:
    if args.verbose:
        print "No demographics file provided; loading information from API."
    demo_cols = ['study_id', 'redcap_event_name', 'sex', 'age', 'mri_xnat_sid']
    general_df = project_entry.export_records(fields=demo_cols,
                                              events=selected_events,
                                              format='df')

    # Need to recode Redcap sex labels because they're not meaningful
    general_df['sex'] = general_df['sex'].map({0: "F", 1: "M"})

    # FIXME: Demographics table and its values only exist at baseline, so 'sex'
    #   has to be explicitly forward-filled within subject. Normally,
    #   assignment from .groupby().fillna(method="ffill") would be appropriate,
    #   but for some reason doesn't work properly in pandas 0.14.

    lookup = get_id_lookup_from_demographics_file(general_df)
    general_df = api_result_to_release_format(general_df, lookup)
else:
    general_df = process_demographics_file(args.demographics_file)
    lookup = get_id_lookup_from_demographics_file(general_df)


## 2. Round age and remove records with uncalculated age
general_df['age'] = general_df['age'].round(decimals=0)
general_df = general_df.dropna(subset=['age'])
general_df['age'] = general_df['age'].astype(int)

form_specifics = get_aseba_form(args.form)

## 3. Extract form-specific info
if not args.input:
    if args.verbose:
        print "No input files provided; loading information from API."
    aseba_df = project_entry.export_records(fields=['study_id'],
                                            events=selected_events,
                                            forms=[form_specifics.form],
                                            format='df')
    aseba_df = api_result_to_release_format(aseba_df, lookup)
else:
    aseba_df = load_redcap_summaries(args.input)

# filter columns so that they start with youthreport1_asr_section
# only keep rows that have at least 100 responses
aseba_df_answers = (aseba_df.filter(regex=form_specifics.form_field_regex)
                    .dropna(axis=0, how='any', thresh=args.threshold)
                    .fillna(value=9))


# Check that all relevant columns were provided and form_field_regex didn't
# under- or over-select
if len(aseba_df_answers.columns) != form_specifics.field_count:
    raise ValueError("%d fields expected for form %s, but only %d present" % (
        form_specifics.field_count,
        args.form.upper(),
        len(aseba_df_answers.columns)
    ))

## 4. Shrink into a single column
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

# NOTE: Provisional, to compare with old output more easily
output_df['redcap_event_name'] = (output_df['visit']
                                  .str.replace('^followup_', '')
                                  + '_visit_arm_1')
output_df.sort(['study_id', 'redcap_event_name'], inplace=True)
output_df = output_df.reset_index(drop=True)

output_df.index.rename('subjectno', inplace=True)
output_df = output_df.reset_index()  # get subjectno as a column

# Assign the constant values required by ADM
# pandas 0.16: output_df = output_df.assign(**form_specifics.constant_fields)
for k, v in form_specifics.constant_fields.items():
    output_df[k] = v

# Rename columns to be reused
output_df = output_df.rename(columns={'study_id': 'firstname',
                                      'mri_xnat_sid': 'middlename',
                                      'redcap_event_name': 'lastname',
                                      'arm': 'othername',
                                      'sex': 'gender'})

# Rearrange existing columns and fill the non-existent one with NaNs
adm_headers = ["admver", "datatype", "subjectno", "id", "firstname",
               "middlename", "lastname", "othername", "gender", "dob",
               "ethniccode", "formver", "dataver", "formno", "formid", "type",
               "enterdate", "dfo", "age", "agemonths", "educcode", "fobcode",
               "fobgender", "fparentses", "fsubjses", "fspouseses",
               "agencycode", "clincode", "bpitems", "compitems", "afitems",
               "otheritems", "experience", "scafitems", "facilityco",
               "numchild", "hours", "months", "schoolname", "schoolcode",
               "tobacco", "drunk", "drugs", "drinks", "ctimecode", "ctypecode",
               "early", "weeksearly", "weight", "lb_gram", "ounces",
               "infections", "nonenglish", "slowtalk", "worried", "spontan",
               "combines", "mlp", "words162", "words310", "otherwords",
               "totwords", "origin", "fudefcode1", "fudefcode2", "sudefcode1",
               "interviewr", "rater", "fstatus", "usertext", "sparentses",
               "ssubjses", "cas", "casfsscr", "das", "dasgcascr", "kabc",
               "kabcmpcscr", "sb5", "sb5fsiqscr", "wj3cog", "wj3cogscr",
               "wais3", "wais3scr", "wisc4", "wisc4scr", "wppsi3", "wppsi3scr",
               "other1test", "othtst1scr", "other2test", "othtst2scr",
               "other3test", "othtst3scr", "other1name", "other2name",
               "other3name", "obstime", "rptgrd", "medic", "medicdesc",
               "dsmcrit", "dsmcode1", "dsmdiag1", "dsmcode2", "dsmdiag2",
               "dsmcode3", "dsmdiag3", "dsmcode4", "dsmdiag4", "dsmcode5",
               "dsmdiag5", "dsmcode6", "dsmdiag6", "illness", "illdesc",
               "speced", "sped1", "sped2", "sped3", "sped4", "sped5", "sped6",
               "sped7", "sped8", "sped9", "sped10", "sped10a", "sped10b",
               "sped10c", "admcatlg", "society", "cethnic", "ceduc", "cfob",
               "cagency", "cclin", "cintervr", "crater", "cfacilit", "ctime",
               "ctype", "cschool", "cfudef1", "cfudef2", "csudef1"]

output_df = output_df.reindex(columns=adm_headers)
output_df.to_csv(args.output, index=False)
