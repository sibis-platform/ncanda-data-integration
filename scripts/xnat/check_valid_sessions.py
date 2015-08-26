#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision$
##  $LastChangedBy$
##  $LastChangedDate$
##
"""
Check Valid Sessions

Check for valid scanning sessions and time windows
"""
__author__ = "Nolan Nichols <http://orcid.org/0000-0003-1099-3328>"
__modified__ = "2015-08-26"

import os

import pandas as pd

import xnat_extractor as xe

verbose = None

# Define global scan types for modalities
t1_scan_types = ['ncanda-t1spgr-v1', 'ncanda-mprage-v1']
t2_scan_types = ['ncanda-t2fse-v1']


def main(args=None):
    if args.update:
        config = xe.get_config(args.config)
        session = xe.get_xnat_session(config)
        xe.extract_experiment_xml(config, session,
                                  args.experimentsdir, args.num_extract)

    # extract info from the experiment XML files
    experiment = xe.get_experiments_dir_info(args.experimentsdir)
    scan = xe.get_experiments_dir_scan_info(args.experimentsdir)
    reading = xe.get_experiments_dir_reading_info(args.experimentsdir)
    df = xe.merge_experiments_scans_reading(experiment, scan, reading)

    # exclude phantoms, including the traveling human phantoms
    site_id_pattern = '[A-E]-[0-9]{5}-[MF]-[0-9]'
    df = df[df.site_id.str.contains(site_id_pattern)]

    # convert to date type
    df.loc[:, 'experiment_date'] = df.experiment_date.astype('datetime64')

    result = pd.DataFrame()
    for subject_id in df.subject_id.drop_duplicates():
        subject_df = df[df.subject_id == subject_id]

        # find the earliest exam date for each given subject
        baseline_date = subject_df.groupby('subject_id')['experiment_date'].nsmallest(1)
        baseline_df = subject_df[subject_df.experiment_date == baseline_date[0]]

        # Find window for follow-up
        followup_min = baseline_df.experiment_date + pd.datetools.Day(n=args.min)
        followup_max = baseline_df.experiment_date + pd.datetools.Day(n=args.max)

        followup_df = subject_df[(subject_df.experiment_date > followup_min[0]) &
                                 (subject_df.experiment_date < followup_max[0])]

        # Create report for baseline visit
        if args.baseline:
            followup_df = baseline_df

        # filter for specific scan types
        t1_df = followup_df[followup_df.scan_type.isin(t1_scan_types)]
        t2_df = followup_df[followup_df.scan_type.isin(t2_scan_types)]

        # add quality column
        t1_usable = t1_df[t1_df.quality == 'usable']
        t2_usable = t2_df[t2_df.quality == 'usable']

        # report columns
        columns = ['site_id', 'subject_id', 'experiment_id',
                   'experiment_date', 'quality', 'excludefromanalysis', 'note']
        t1_recs = t1_usable.loc[:, columns].to_records(index=False)
        t2_recs = t2_usable.loc[:, columns].to_records(index=False)

        t1_report = pd.DataFrame(t1_recs, index=t1_usable.experiment_id)
        t2_report = pd.DataFrame(t2_recs, index=t2_usable.experiment_id)

        t1_t2_report = t1_report.join(t2_report.quality,
                                      lsuffix='_t1',
                                      rsuffix='_t2',
                                      how='inner')
        if t1_t2_report.shape[0]:
            result = result.append(t1_t2_report)

    result.to_csv(args.outfile)

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(prog='check_valid_sessions.py',
                                     description=__doc__)
    parser.add_argument('-c', '--config',
                        type=str,
                        default=os.path.join(os.path.expanduser('~'),
                                             '.server_config', 'ncanda.cfg'))
    parser.add_argument('-b', '--baseline',
                        action='store_true',
                        help='Create report for baseline visit.')
    parser.add_argument('-e', '--experimentsdir',
                        type=str,
                        default='/tmp/experiments',
                        help='Name of experiments xml directory')
    parser.add_argument('--min',
                        type=int,
                        default=180,
                        help='Minimum days from baseline')
    parser.add_argument('--max',
                        type=int,
                        default=540,
                        help='Maximum days from baseline')
    parser.add_argument('-o', '--outfile',
                        type=str,
                        default='/tmp/usable_t1_t2_baseline.csv',
                        help='Name of csv file to write.')
    parser.add_argument('-n', '--num_extract',
                        type=int,
                        help='Number of sessions to extract')
    parser.add_argument('-u', '--update',
                        action='store_true',
                        help='Update the cache of xml files')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Print verbose output.')
    argv = parser.parse_args()
    verbose = argv.verbose
    xe.verbose = argv.verbose

    sys.exit(main(args=argv))
