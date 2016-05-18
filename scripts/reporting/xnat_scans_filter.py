#!/usr/bin/env python
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
xnat_scans_filter.py
======================
This script filters the csv file generated using xnat_extractor.py. This filters
is based on records from XNAT where there is one row per scan.

xnat_scans_filter.py -i path/to/xnat.csv
"""

import os
import sys

import redcap
import pandas as pd

# Fields to retrieve from REDCap
fields = ['study_id', 'redcap_event_name', 'exclude', 'visit_ignore',
          'visit_date', 'mri_missing', 'mri_xnat_sid', 'mri_xnat_eids',
          'visit_notes']

# Forms that the fields come from in REDCap.
forms = ['mr_session_report', 'visit_date', 'demographics']


def get_project_entry(args=None):
    """
    Pulls the data from REDCap
    """
    # Get API key.
    summary_key_file = open(os.path.join(os.path.expanduser("~"),
                                         '.server_config',
                                         'redcap-dataentry-token'), 'r')
    summary_api_key = summary_key_file.read().strip()

    # Connect to API.
    project_entry = redcap.Project('https://ncanda.sri.com/redcap/api/',
                                   summary_api_key,
                                   verify_ssl=False)
    return project_entry


def data_entry_fields(fields, project, arm):
    """
    Gets the dataframe containing a specific arm from REDCap
    """
    # Get a dataframe of fields
    data_entry_raw = project.export_records(fields=fields,
                                            forms=forms,
                                            format='df',
                                            events=[arm])
    return data_entry_raw


def append_site_id_row(xnat_df, scans_df):
    scans_df['site_id'] = ''
    ids = xnat_df[['site_id', 'subject_id']]
    map = {r.subject_id: r.site_id for idx, r in ids.iterrows()}
    for idx, row in scans_df.iterrows():
        scans_df.site_id.loc[idx] = map.get(row.case)
    return scans_df


def is_in_redcap(rc_df, scans_df):
    """
    Checks if the scans missing in the pipeline are listed in REDCap and adds
    a column indicating as such.
    """
    scans_df['in_redcap'] = False
    scans_df['visit_ignore___yes'] = ''
    scans_df['visit_ignore_why'] = ''
    scans_df['visit_ignore_why_other'] = ''
    scans_df['visit_notes'] = ''
    scans_df['mri_missing'] = ''
    scans_df['mri_missing_why'] = ''
    scans_df['mri_missing_why_other'] = ''
    scans_df['mri_notes'] = ''
    rc_cases = rc_df[rc_df.mri_xnat_sid.isin(scans_df.case)]
    for idx, row in rc_cases.iterrows():
        scan_cases = scans_df[scans_df.case == row.mri_xnat_sid]
        scans_df.in_redcap.loc[scan_cases.index] = True
        # Visit info
        scans_df.visit_ignore___yes.loc[scan_cases.index] = row.visit_ignore___yes
        scans_df.visit_ignore_why.loc[scan_cases.index] = row.visit_ignore_why
        scans_df.visit_ignore_why_other.loc[scan_cases.index] = row.visit_ignore_why_other
        scans_df.visit_notes.loc[scan_cases.index] = row.visit_notes
        # Scan info
        scans_df.mri_missing.loc[scan_cases.index] = row.mri_missing
        scans_df.mri_missing_why.loc[scan_cases.index] = row.mri_missing_why
        scans_df.mri_missing_why_other.loc[scan_cases.index] = row.mri_missing_why_other
        scans_df.mri_notes.loc[scan_cases.index] = row.mri_notes
    return scans_df


def is_in_xnat(xnat_df, scans_df):
    """
    Checks XNAT for scans near the visit date recorded in REDCap
    """


def main(args=None):
    # Connect to REDCap
    project_entry = get_project_entry()

    # Get the visit dataframe
    project_df = data_entry_fields(fields, project_entry, args.event)

    # Get a list of all EIDs for the given visit
    xnat_eids = project_df['mri_xnat_eids'].tolist()

    # Read the csv file from xnat_extractor
    xnat_csv = pd.read_csv(args.infile)

    # Filter the XNAT records by the EIDs in REDCap
    # This provides a list of all the scans in XNAT that are also in REDCap
    filter_csv = xnat_csv[xnat_csv['experiment_id'].isin(xnat_eids)]

    # Iterate through scans missing in the pipeline and check:
    #   - they are present in the filtered REDCap list
    # present in the REDCap filter list.
    if args.missing_scans:
        list_missing_scans = pd.read_csv(args.missing_scans)
        missing_scans_df = append_site_id_row(xnat_csv, list_missing_scans)

        # Add columns indicating if there is data for this visit in redcap
        in_redcap = is_in_redcap(project_df, missing_scans_df)
        filter_csv = in_redcap

    # Write the results to disk
    filter_csv.to_csv(args.outfile)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--infile',
                        required=True,
                        help="Input csv file from xnat_extractor.py")
    parser.add_argument('-e', '--event',
                        choices=['baseline_visit_arm_1', '1y_visit_arm_1'],
                        default='1y_visit_arm_1')
    parser.add_argument('-m', '--missing-scans',
                        help="Output of list_missing_scans script.")
    parser.add_argument('-o', '--outfile',
                        default=os.path.join('/tmp', 'xnat_scans_filter.csv'))
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose reporting.')
    argv = parser.parse_args()
    sys.exit(main(args=argv))
