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
args = parser.parse_args()

data = pandas.read_excel(args.input, sheet_name=0)  # return first sheet

# Rename the columns per definition in aseba_form and only keep those columns
form_specifics = get_aseba_form(args.form)
dict_renames = form_specifics.post_score_renames
data = data.rename(columns=dict_renames)
data = data.loc[:, dict_renames.values()]

# Modify the metadata columns
data.loc[data['arm'].isnull(), 'arm'] = 'standard'
data['visit'] = data['visit'].str.replace('_arm_1', '')

data.to_csv(args.output, index=False)
