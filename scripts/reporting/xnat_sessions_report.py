#!/usr/bin/env python

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
"""
XNAT Sessions Report

Check for valid scanning sessions and time windows by first caching all the
XNAT session XML files and then parsing these files for necessary info. Note
that to create the XML file cache you need to run with --update

Example
=======
- When running for the first time run 
  ./xnat_sessions_report.py --update
  so that the cach (located at experimentsdir) is created 

- Update the cache (stored in experimentsdir) and generate the baseline report
  ./xnat_sessions_report.py --update --baseline

- Use the existing cache to extract 10 in the followup window
 ./xnat_sessions_report.py --num_extract 10 --min 180 --max 540
"""
__author__ = "Nolan Nichols <http://orcid.org/0000-0003-1099-3328>"
__modified__ = "2016-05-09"

import os

import pandas as pd

import xnat_extractor as xe

verbose = None


def get_scan_type_pairs(modality):
    """
    Get a dictionary of series description based on modality
    :param modality: str (anatomy, diffusion, functional)
    :return: dict
    """
    scan_type_pairs = dict(scan1=None, scan2=None)
    if modality == 'anatomy':
        t1_scan_types = ['ncanda-t1spgr-v1', 'ncanda-mprage-v1']
        t2_scan_types = ['ncanda-t2fse-v1']
        scan_type_pairs.update(scan1=t1_scan_types,
                               scan2=t2_scan_types)
    elif modality == 'diffusion':
        pepolar = ['ncanda-dti6b500pepolar-v1']
        dwi = ['ncanda-dti60b1000-v1']
        scan_type_pairs.update(scan1=pepolar,
                               scan2=dwi)
    elif modality == 'functional':
        fmri = ['ncanda-rsfmri-v1']
        fieldmap = ['ncanda-grefieldmap-v1']
        scan_type_pairs.update(scan1=fmri,
                               scan2=fieldmap)
    return scan_type_pairs


def main(args=None):
    # TODO: Handle when T1 and T2 are in separate session (i.e., rescan)
    if args.update:
        config = xe.get_config(args.config)
        session = xe.get_xnat_session(config)
        xe.extract_experiment_xml(config, session,
                                  args.experimentsdir, args.num_extract)

    # extract info from the experiment XML files
    experiment = xe.get_experiments_dir_info(args.experimentsdir)
    # Scan specific information 
    scan = xe.get_experiments_dir_scan_info(args.experimentsdir)
    # Session info 
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
        grouping = subject_df.groupby('subject_id')
        baseline_date = grouping['experiment_date'].nsmallest(1)
        baseline_df = subject_df[subject_df.experiment_date == baseline_date[0]]

        # Find window for follow-up
        day_min = pd.datetools.Day(n=args.min)
        day_max = pd.datetools.Day(n=args.max)
        followup_min = baseline_df.experiment_date + day_min
        followup_max = baseline_df.experiment_date + day_max

        df_min = subject_df.experiment_date > followup_min[0]
        df_max = subject_df.experiment_date < followup_max[0]
        followup_df = subject_df[df_min & df_max]

        # Included followup sessions slightly outside window
        included = ['NCANDA_E02615', 'NCANDA_E02860']
        included_df = subject_df[subject_df.experiment_id.isin(included)]
        if included_df.shape[0]:
            followup_df = included_df

        # Create report for baseline visit
        if args.baseline:
            followup_df = baseline_df

        # filter for specific scan types
       
        scan_type_pairs = get_scan_type_pairs(args.modality)
        scan1 = scan_type_pairs.get('scan1')
        scan2 = scan_type_pairs.get('scan2')
        scan1_df = followup_df[followup_df.scan_type.isin(scan1)]
        scan2_df = followup_df[followup_df.scan_type.isin(scan2)]

        # Filter quality column
        if args.usable : 
            scan1_selected = scan1_df[scan1_df.quality == 'usable']
            scan2_selected = scan2_df[scan2_df.quality == 'usable']
        else : 
            scan1_selected = scan1_df
            scan2_selected = scan2_df

        # report columns
        columns = ['site_id', 'subject_id', 'experiment_id', 'experiment_date',
                   'excludefromanalysis', 'note', 'scan_type', 'quality',
                   'scan_note']
        scan1_recs = scan1_selected.loc[:, columns].to_records(index=False)
        scan2_recs = scan2_selected.loc[:, columns].to_records(index=False)

        scan1_report = pd.DataFrame(scan1_recs,
                                    index=scan1_selected.experiment_id)
        scan2_report = pd.DataFrame(scan2_recs,
                                    index=scan2_selected.experiment_id)

        scan1_scan2_report = scan1_report.join(scan2_report[['scan_type',
                                                             'quality',
                                                             'scan_note']],
                                               lsuffix='_scan1',
                                               rsuffix='_scan2',
                                               how='inner')
        if scan1_scan2_report.shape[0]:
            result = result.append(scan1_scan2_report)
    # Remove any duplicate rows due to extra usable scan types (i.e., fieldmaps)
    result = result.drop_duplicates()
    result.to_csv(args.outfile, index=False)

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(prog='xnat_sessions_report.py',
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
    parser.add_argument('-m', '--modality',
                        type=str,
                        default='anatomy',
                        choices=['anatomy', 'diffusion', 'functional'],
                        help='Name of experiments xml directory')
    parser.add_argument('--min',
                        type=int,
                        default=180,
                        help='Minimum days from baseline (to specify followup '
                             '1y, only impacts final report but not -u option)')
    parser.add_argument('--max',
                        type=int,
                        default=540,
                        help='Maximum days from baseline (to specify followup '
                             '1y, only impacts final report but not -u option)')
    parser.add_argument('--usable',
                        action='store_true',
                        help='Only list scans with usable image quality')

    parser.add_argument('-o', '--outfile',
                        type=str,
                        default='/tmp/usability_report.csv',
                        help='Name of csv file to write.')
    parser.add_argument('-n', '--num_extract',
                        type=int,
                        help='Number of sessions to extract (only works in '
                             'connection with -u)')
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
