#!/usr/bin/env python
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Creates a csv files containing all visits of cases included in the study. Run -h for options 

Usage:
python create_redcap_visit_list.py 
"""
import os
import sys
from sibispy import sibislogger as slog
import sibispy

import redcap

def get_project(rc_summary,event_list):
    # Get all the mri session reports
    if len(event_list):
        mri  = rc_summary.export_records(fields=['study_id', 'exclude',
                                                 'visit_ignore___yes'],
                                         forms=['mr_session_report', 'visit_date',
                                                'demographics'],
                                         events=event_list.split(","),
                                         format='df')
    else :
        mri  = rc_summary.export_records(fields=['study_id', 'exclude',
                                                 'visit_ignore___yes'],
                                         forms=['mr_session_report', 'visit_date',
                                                'demographics'],
                                         format='df')
    return mri

def main(args=None):
    if args.verbose:
        print("Connecting to REDCap...")

    if args.all_events:
        args.event = ""


    slog.init_log(False, False,'create_redcap_visit_list', 'create_redcap_visit_list',None)
    session = sibispy.Session()
    if not session.configure():
        if args.verbose:
            print "Error: session configure file was not found"

        sys.exit()

    rc_summary = session.connect_server('data_entry', True)
    if not rc_summary :
        if args.verbose:
            print "Error: Could not connect to Redcap for Import Project"

        sys.exit()


    project = get_project(rc_summary,args.event)
    if args.verbose:
        print("Filtering dataframe...")

    project = project[project.exclude != 1]
    if args.subjectlist:
        with open(args.subjectlist, 'r') as f:
            subject_list = [line.strip() for line in f]

        project_base = project[project.index.map( lambda key: key[1] == "baseline_visit_arm_1" )]
        if len(project_base.index.values) == 0 :
            print "Error: event baseline_visit_arm_1 needs to be part of search"
            sys.exit(0)

        project_base_subject = project_base[project_base.mri_xnat_sid.isin(subject_list) ]
        subject_rid_list=  [ x[0] for x in project_base_subject.index.values ]
        project = project[project.index.map( lambda key: key[0] in subject_rid_list )]

    if args.verbose:
        print("Writing results to {}...".format(args.outfile))
    # Write out results
    project.to_csv(args.outfile,columns=args.fields.split(","))

if __name__ == '__main__':
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="baseline_1yr_cases.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('-e', '--event', dest="event", action='store',
                        default="baseline_visit_arm_1,1y_visit_arm_1,2y_visit_arm_1,3y_visit_arm_1",
                        help="A list containg the events of interest. {}".format(default))
    parser.add_argument('--all-events', help="Download data from all events", action='store_true')
    parser.add_argument('-f', '--fields', dest="fields",
                        default="visit_ignore___yes,mri_missing,visit_date,mri_xnat_sid,mri_xnat_eids,mri_series_t1,mri_series_t2,mri_series_dti6b500pepolar,mri_series_dti60b1000,mri_series_dti_fieldmap,mri_series_rsfmri,mri_series_rsfmri_fieldmap",
                        help="A list containing the fields to be printed out. {}".format(default),
                        action='store')
    parser.add_argument('-o', '--outfile', dest="outfile",
                        help="File to write out. {}".format(default),
                        default='baseline_1yr_cases.csv')
    parser.add_argument('-s', '--subjectlist', dest="subjectlist",
                        help="Text file containing the SIDS for subjects of interest", action='store')
    parser.add_argument('-v', '--verbose', dest="verbose",
                        help="Turn on verbose", action='store_true')
    argv = parser.parse_args()
    sys.exit(main(args=argv))
