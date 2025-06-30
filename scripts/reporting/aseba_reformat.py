#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Transform an Excel file produced by ASEBA scoring to an NCANDA release format.

```bash
# In this example, the xlsx files are names ASR_Scored_2018-08.xlsx, etc.
ASEBA_FOLDER=/fs/ncanda-share/beta/simon/aseba_082018
for form in asr ysr cbc; do
  ./aseba_reformat.py --form $form \
    --input ${ASEBA_FOLDER}/${form^^}_Scored_2018-08.xlsx \
    --output ${ASEBA_FOLDER}/${form}_scored.csv
done
```
"""
import sys
import pandas
import argparse
from aseba_form import get_aseba_form

def parse_args(input_args=None):
    parser = argparse.ArgumentParser(
        description="Reformat the output of ASEBA scoring for a particular form.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-i', '--input', help="xlsx filename to process.",
                        action="store", required=True)
    parser.add_argument('-o', '--output', help="CSV file to write output to.",
                        action="store", default=sys.stdout)
    parser.add_argument('-f', '--form',
                        choices=["asr", "ysr", "cbc"],
                        help="ASEBA form to extract the raw values for",
                        required=True)
    parser.add_argument('-v', '--verbose',
                        help="Print diagnostic info to stdout",
                        action="store_true")
    return parser.parse_args(input_args)


if __name__ == "__main__":
    args = parse_args()
    data = pandas.read_excel(args.input, sheet_name=0)  # return first sheet

    # Rename the columns per definition in aseba_form and only keep those columns
    form_specifics = get_aseba_form(args.form)
    dict_renames = form_specifics.post_score_renames
    data = data.rename(columns=dict_renames)
    actual_columns = [x for x in dict_renames.values() if x in data.columns]
    missed_columns = [(k, v) for k, v in dict_renames.items()
                      if v not in data.columns]
    dropped_columns = [x for x in data.columns if x not in actual_columns]
    if args.verbose:
        print("Missed columns: ", missed_columns)
        print("Unmatched (and therefore dropped) columns: ", dropped_columns)
    data = data.loc[:, actual_columns]

    # Modify the metadata columns
    if 'arm' in data.columns:
        data.loc[data['arm'].isnull(), 'arm'] = 'standard'
    else:
        data['arm'] = 'standard'

    if data['visit'].str.contains('_visit_arm_1', na=False).any():
        data['visit'] = (data['visit']
                         .str.replace('_visit_arm_1', '')
                         .str.replace(r'^(\dy)$', r'followup_\1', regex=True))

    # Cheap way to ensure that these three columns come first
    index_fields = ['subject', 'arm', 'visit']
    data.set_index(index_fields, inplace=True)
    data.sort_index(inplace=True)

    try:
        data.to_csv(args.output, index=True)
    except IOError:  # e.g. when writing to stdout that's suddenly closed
        pass
