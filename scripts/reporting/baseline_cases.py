#!/usr/bin/env python
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Baseline cases
==============
This script generates a list of all subject that have a valid baseline.

Usage:
python baseline_cases.py
"""
from __future__ import print_function
import os

import pandas
import redcap

def get_project(args):
    # First REDCap connection for the Summary project (this is where we put data)
    summary_key_file = open(os.path.join( os.path.expanduser("~"), '.server_config/redcap-dataentry-token' ), 'r')
    summary_api_key = summary_key_file.read().strip()
    rc_summary = redcap.Project('https://ncanda.sri.com/redcap/api/', summary_api_key, verify_ssl=False)

    # Get all np reports for baseline and 1r
    visit  = rc_summary.export_records(fields=['study_id', 'exclude',
                                               'visit_ignore___yes'],
                                       forms=['mr_session_report','visit_date'],
                                       events=['baseline_visit_arm_1'],
                                       format='df')
    return visit

def np_filter_dataframe(dataframe):
    # Create filters for cases that are included
    case_included = dataframe.exclude != 1 # subject excluded from NCANDA Study
    visit_included = dataframe.visit_ignore___yes != 1 # subject did not have a valid visit for this event

    # Apply filters for results
    included = dataframe[case_included]
    results = included[visit_included]
    return results

def main(args):
    if args.verbose:
        print("Connecting to REDCap...")
    project = get_project(args)
    if args.verbose:
        print("Filtering dataframe...")
    if args.subjectlist:
        with open(args.subjectlist, 'r') as f:
            subject_list = [line.strip() for line in f]
        project = project[project['mri_xnat_sid'].isin(subject_list)]
    results = np_filter_dataframe(project)
    if args.verbose:
        print("Writing results to {}...".format(args.outfile))
    # Write out results
    results.to_csv(os.path.join(args.csvdir, args.outfile), columns = ['exclude',
                   'visit_ignore___yes', 'mri_xnat_sid','mri_xnat_eids'])

if __name__ == '__main__':
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="baseline_cases.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('-c', '--csvdir',  action="store", default = '',
                        help="Directory where CSV will be stored.")
    parser.add_argument('-o', '--outfile', dest="outfile",
                        help="File to write out. {}".format(default),
                        default='baseline_1yr_cases.csv')
    parser.add_argument('-v', '--verbose', dest="verbose",
                        help="Turn on verbose", action='store_true')
    argv = parser.parse_args()
    sys.exit(main(args=argv))
