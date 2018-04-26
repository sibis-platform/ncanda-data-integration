#!/usr/bin/env python
# """
# Given a CSV with the current data dictionary and a list of patch files with
# updated / newly inserted variables, produce a full patched data dictionary.
# """
import sys
import pandas as pd
import csv
import argparse

from datadict_utils import load_datadict, insert_rows_at

parser = argparse.ArgumentParser(
    description="Apply patches to the current data dictionary.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('-c', '--current',
                    help="CSV file with the current data dictionary",
                    action="store", required=True,
                    type=argparse.FileType('r'))
parser.add_argument('-o', '--output',
                    help="CSV file to write output in.",
                    action="store",
                    default=sys.stdout)
parser.add_argument('patch_files', help="CSV file(s) with patch for datadict",
                    nargs='+',
                    type=argparse.FileType('r'),
                    action="store")
parser.add_argument('-v', '--verbose',
                    help="Write to stdout what the script is doing",
                    action="store_true")
parser.add_argument('--update-only',
                    help="Do not add any new variables.",
                    action="store_true")

# TODO: Instead of "do not update", enhance logic to "do not overwrite"
parser.add_argument('--skip-branching',
                    help="Do not update branching logic information.",
                    action="store_true")
parser.add_argument('--skip-section-headers',
                    help="Do not update section headers.",
                    action="store_true")
parser.add_argument('--skip-field-notes',
                    help="Do not update field notes.",
                    action="store_true")

# TODO: Implement
parser.add_argument('--keep-options',
                    help=("Prevent the patch from downgrading Field Type to "
                          "text and/or removing options"),
                    action="store_true")
# TODO: Trimming options

args = parser.parse_args()

dd = load_datadict(args.current)
dd_columns = dd.columns.tolist()  # To preserve order

# 0. For each patch file:
for patch_file in args.patch_files:
    patch_df = load_datadict(patch_file, trim_all=True)
    existing_rows = dd.index.intersection(patch_df.index)
    new_rows = patch_df.index.difference(dd.index)
    if args.verbose:
        print "\nProcessing %s:" % patch_file.name
        print "Updating the following columns:"
        print existing_rows.tolist()
        if args.update_only:
            print "Ignoring the following new columns:"
        else:
            print "Inserting the following new columns:"
        print new_rows.tolist()

    # 1. In the patch, find the entries that already exist and simply rewrite
    #       them
    # 
    # TODO: Implement overwriting only a subset of values
    overwrite_columns = set(dd.columns)
    if args.skip_branching:
        overwrite_columns = overwrite_columns - set(["Branching Logic (Show field only if...)"])
    if args.skip_section_headers:
        overwrite_columns = overwrite_columns - set(["Section Header"])
    if args.skip_field_notes:
        overwrite_columns = overwrite_columns - set(["Field Note"])

    if len(existing_rows) > 0:
        dd.loc[existing_rows, overwrite_columns] = patch_df.loc[existing_rows, overwrite_columns]

    # 2. If there were new entries:
    if (len(new_rows) > 0) and (not args.update_only):
        # 2a. If there were existing entries, try smart placement of the new
        #       variables
        if len(existing_rows) > 0:  # Try smart placement of new entries
            buffer_new = []
            last_old = None
            for colname, _ in patch_df.iterrows():
                # Check if it's an existing row; if it is, mark it
                if colname in existing_rows:
                    if len(buffer_new) > 0:
                        if last_old is None:
                            # We must insert before this variable
                            insert_before = True
                        else:
                            # We can insert after the last found variable
                            insert_before = False

                        # Insert buffer_new
                        dd = insert_rows_at(dd, colname,
                                            patch_df.loc[buffer_new],
                                            insert_before)
                        buffer_new = []

                    # Reset last_old
                    last_old = colname
                else:
                    # It's a new one -> put it in the buffer
                    buffer_new.append(colname)

        # 2b. If there were no already-existing entries, append the new entries
        #       to the end of the form (or whatever CLI says)
        else:  # No existing entries to append to
            forms = patch_df['Form Name'].unique().tolist()

            # Find the shared form name (if possible) and append to its end
            for form in forms:
                if dd['Form Name'].str.contains(form).any():
                    insertion_point = dd[dd['Form Name'] == form].index[-1]
                else:
                    insertion_point = dd.index[-1]

                dd = insert_rows_at(dd, insertion_point,
                                    patch_df[patch_df['Form Name'] == form])

# Write out the updated data dictionary (with correctly ordered entries)
dd[dd_columns].to_csv(args.output, quoting=csv.QUOTE_NONNUMERIC)
