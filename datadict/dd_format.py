#!/usr/bin/env python
"""
Reformats data dictionary files to conform with NCANDA / REDCAP style.

Currently, this means changing any newlines within fields to carriage returns.
"""
import pandas as pd
import argparse
import sys
import csv

parser = argparse.ArgumentParser(
    description="Ensure valid CSV data dictionary for REDCap.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('-i', '--input', help="CSV file to process.",
                    action="store")
parser.add_argument('-o', '--out', help="CSV file to write output in.",
                    action="store", default=sys.stdout)
args = parser.parse_args()

if args.input:
    input_dd = pd.read_csv(args.input)
    input_dd = input_dd.apply(lambda x: x.str.replace('\n', '\r'), axis=1)
else:
    raise ValueError('No input file provided!')

input_dd.to_csv(args.out, index=False, quoting=csv.QUOTE_NONNUMERIC)
