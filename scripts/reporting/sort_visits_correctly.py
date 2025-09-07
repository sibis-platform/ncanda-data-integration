#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Sorts the visits so that they are in order baseline, followup_1y , ... , followup_10y .

```bash
  ./sort_visits_correctly.py  input.csv  output.csv
done
```
"""

import argparse
import math
import re
import sys
import pandas as pd


def parse_args(input_args=None):
    parser = argparse.ArgumentParser(
        description="Ensuring that visits are correctly formatted.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('input_csv', help="csv input filename to process.")
    parser.add_argument('output_csv', help="CSV file to write output to.")
    return parser.parse_args(input_args)


def visit_key(v):
    """
    Map visit labels to a sortable (group, number) key:
      baseline -> (0, 0)
      followup_#y -> (1, #)   (numeric-aware)
      anything else -> (2, +inf) so it sorts after the known ones
    """
    if pd.isna(v):
        return (3, math.inf)

    s = str(v).strip().lower()
    if s in {"baseline", "bl"}:
        return (0, 0)

    m = re.fullmatch(r"followup[_-]?(\d+)y?", s)
    if m:
        return (1, int(m.group(1)))
    
    # Anything else that does not follow baseline or followup_*y is put at end of list 
    return (2, math.inf)


if __name__ == "__main__":
    args = parse_args()
    
    df = pd.read_csv(args.input_csv, dtype=str)  # keep raw values as strings

    # Safety checks
    required_cols = {"subject", "arm", "visit"}
    missing = required_cols - set(df.columns)
    if missing:
        sys.exit(f"ERROR: Missing required columns: {', '.join(sorted(missing))}")

    # Build sortable keys
    visit_keys = df["visit"].map(visit_key)
    df["_visit_group"] = [g for g, _ in visit_keys]
    df["_visit_num"] = [n for _, n in visit_keys]

    # Stable sort: subject, arm (lexicographic), then visit (group, number)
    df_sorted = df.sort_values(
        by=["subject", "arm", "_visit_group", "_visit_num"],
        kind="mergesort"  # stable
    ).drop(columns=["_visit_group", "_visit_num"])

    df_sorted.to_csv(args.output_csv, index=False)
    
