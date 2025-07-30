#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Check Missing Scans
===================
- Take as input a csv file containing subject id, visit, and validation type.
- Then query redcap to see if scan information is available for validation type.
- If there is info, gather the relevant scan identifiers, then query xnat
- If there isn't info, get the visit date and check xnat for any scans within a window.

Usage
-----

"""
from __future__ import print_function

import os
import sys

import redcap
import pandas as pd

from sibispy.xnat_util import get_xnat_util

event_mapping = dict(baseline='baseline_visit_arm_1',
                     followup_1y='1y_visit_arm_1',
                     followup_2y='2y_visit_arm_1')


def parse_csv(in_file):
    csv = pd.read_csv(in_file)
    required_columns = ['subject_id', 'visit_id', 'error_type']
    for column in required_columns:
        if column not in csv.columns:
            raise IndexError('Required column not present: {}'.format(column))
    return csv


def main(args=None):
    if args.verbose:
        print("Validating input csv.")
    csv = parse_csv(args.input)

    # currently just working with one visit
    event = event_mapping.get(csv.visit_id.get(0))

    if args.verbose:
        print("Creating connection...")
    dataentry_key_file = open(os.path.join(os.path.expanduser("~"),
                                           '.server_config',
                                           'redcap-dataentry-token'), 'r')
    dataentry_api_key = dataentry_key_file.read().strip()
    project_entry = redcap.Project('https://ncanda.sri.com/redcap/api/',
                                   dataentry_api_key,
                                   verify_ssl=False)
    mri_form = project_entry.export_records(forms=['mr_session_report'],
                                            events=[event],
                                            fields=['subject_id'],
                                            format_type='df')
    visit_form = project_entry.export_records(forms=['visit'],
                                              events=[event],
                                              fields=['visit_ignore', 'visit_ignore_why'],
                                              format_type='df')
    # These are subject ids from the list that are in REDCap.
    rc_filter = mri_form.mri_xnat_sid.isin(csv.subject_id)
    rc_cases = mri_form[rc_filter]

    # These are the cases that are not in REDCap (i.e., missing sessions)
    non_rc_filter = ~csv.subject_id.isin(rc_cases.mri_xnat_sid)
    non_rc_cases = csv[non_rc_filter]


    # now look up what info is on xnat
    # Create interface using stored configuration
    util = get_xnat_util()
    ifc = util.connect()

    print(visit_form)

if __name__ == "__main__":
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="check_missing_scans.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('-i', '--input',
                        required=True,
                        help="A csv file. {}".format(default))
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Turn on verbose mode. {}'.format(default))
    argv = parser.parse_args()
    sys.exit(main(args=argv))
