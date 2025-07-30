#!/usr/bin/env python
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Report: Baseline and Year 1 Cases with Scans
============================================
Creates a csv files containing all cases that are included in the study. Using
flags, one can select which datapoints they are interested in.

Flags -b and -f allow for selecting between basline and 1y follow-up respectively.

Flags -n and -m allow for selection of subjects with a valid visit or a valid
visit with scan session, respectively.

Flag -s creates a report from subset of subjects. The list of subjects should be
entered in a txt file and contain their NCANDA subject ids.

Usage:
python baseline_1yr_cases.py -b -n
"""
from __future__ import print_function
import os
import sys

import redcap

def get_project(args):
    # First REDCap connection for the Summary project (this is where we put data)
    summary_key_file = open(os.path.join(os.path.expanduser("~"),
                                         '.server_config/redcap-dataentry-token' ),
                                          'r')
    summary_api_key = summary_key_file.read().strip()
    rc_summary = redcap.Project('https://ncanda.sri.com/redcap/api/',
                                summary_api_key,
                                verify_ssl=False)

    # Get all the mri session reports for baseline and 1r
    mri  = rc_summary.export_records(fields=['study_id', 'exclude',
                                             'visit_ignore___yes', 'mri_missing'],
                                     forms=['mr_session_report', 'visit_date',
                                            'demographics'],
                                     events=args.event.split(","),
                                     format_type='df')
    return mri

def mri_filter_dataframe(dataframe):
    # Create filters for cases that are included
    case_included = dataframe.exclude != 1 # baseline has 'exclude' in demographics
    visit_included = dataframe.visit_ignore___yes != 1 # Not consistent with 'exclude'
    mri_collected = dataframe.mri_missing != 1

    # Apply filters for results
    included = dataframe[case_included]
    results = included[mri_collected]
    return results

def np_filter_dataframe(dataframe):
    # Create filters for cases that are included
    case_included = dataframe.exclude != 1 # subject excluded from NCANDA Study
    visit_included = dataframe.visit_ignore___yes != 1 # subject did not have a valid visit for this event

    # Apply filters for results
    included = dataframe[case_included]
    results = included[visit_included]
    return results

def main(args=None):
    if args.verbose:
        print("Connecting to REDCap...")
    project = get_project(args)
    if args.verbose:
        print("Filtering dataframe...")
    if args.subjectlist:
        with open(args.subjectlist, 'r') as f:
            subject_list = [line.strip() for line in f]
        project = project[project['mri_xnat_sid'].isin(subject_list)]
    if args.mri_cases:
        results = mri_filter_dataframe(project)
    elif args.np_cases:
        results = np_filter_dataframe(project)
    else:
        results = project
    if args.verbose:
        print("Writing results to {}...".format(args.outfile))
    # Write out results
    results.to_csv(os.path.join(args.csvdir, args.outfile),
                   columns=args.forms.split(", "))

if __name__ == '__main__':
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="baseline_1yr_cases.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument( '-c','--csvdir',  action="store", default = '',
                        help="Directory where CSV will be stored.")
    parser.add_argument('-e', '--event', dest="event", action='store',
                        default="baseline_visit_arm_1,1y_visit_arm_1",
                        help="A list containg the events of interest. {}".format(default))
    parser.add_argument('-f', '--forms', dest="forms",
                        default="visit_ignore___yes, mri_missing, mri_xnat_sid, mri_xnat_eids",
                        help="A list containing the forms of interest. {}".format(default),
                        action='store')
    parser.add_argument('-m', '--mri_cases', dest="mri_cases", action='store_true',
                        help="Generate report for subjects with valid visit & MRI session")
    parser.add_argument('-n', '--np_cases', dest="np_cases", action='store_true',
                        help="Generate report for subjects with valid visit session")
    parser.add_argument('-o', '--outfile', dest="outfile",
                        help="File to write out. {}".format(default),
                        default='baseline_1yr_cases.csv')
    parser.add_argument('-s', '--subjectlist', dest="subjectlist",
                        help="Text file containing the SIDS for subjects of interest", action='store')
    parser.add_argument('-v', '--verbose', dest="verbose",
                        help="Turn on verbose", action='store_true')
    argv = parser.parse_args()
    sys.exit(main(args=argv))
