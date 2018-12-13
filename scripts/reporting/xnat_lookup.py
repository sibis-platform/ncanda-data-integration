#!/usr/bin/env python
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
XNAT ID lookup script for converting between site ids and case ids

Usage
-----
xnat_lookup.py B-00149-M-0
NCANDA_S00236

xnat_lookup.py --print-keys --reverse-lookup NCANDA_S00236
NCANDA_S00236,B-00149-M-0
"""
from __future__ import print_function
import os

import sibispy
from sibispy import sibislogger as slog

verbose = None


def main(args=None):
    """Main program loop

    Args:
        args (object): An attributed dict like argparse.Namespace.

    Returns:
        None
    """

    # Create interface using stored configuration
    slog.init_log(False, False,'xnat_sesions_report', 'xnat_sesions_report',None)
    session = sibispy.Session()
    session.configure()
    if not session.configure() :
        if args.verbose:
            print("Error: session configure file was not found")
        sys.exit()

    ifc = session.connect_server('xnat', True)
    if not ifc:
        print("Error: could not connect to xnat server!") 
        sys.exit()

    if args.reverse_lookup:
        search_field = 'xnat:subjectData/SUBJECT_ID'
        result_idx = 2
    else:
        search_field = 'xnat:subjectData/SUBJECT_LABEL'
        result_idx = 0

    if args.print_project:
        result_idx = 1

    fields_per_subject = ['xnat:subjectData/SUBJECT_ID',
                          'xnat:subjectData/PROJECT',
                          'xnat:subjectData/SUBJECT_LABEL']
    output = ""
    for search in args.search:
        pattern = (search_field, 'LIKE', '%' + search + '%')
        subjects = ifc.search('xnat:subjectData',
                              fields_per_subject).where([pattern]).items()
        if args.print_keys:
            if len(subjects) > 0:
                fmt = '{0},{1}'
                res = [fmt.format(search,
                                  record[result_idx]) for record in subjects]
                output += '\n'.join(res)
            else:
                output += ''.join(search + ',\n')
        else:
            res = ['{0}\n'.format(record[result_idx]) for record in subjects]
            output += ''.join(res)
    if args.outfile:
        with open(args.outfile, 'w') as fi:
            fi.write("case_id, site_id\n")
            fi.write(output)
            fi.close()
        if verbose:
            print(output)
    else:
        print(output)

if __name__ == "__main__":
    import sys
    import argparse

    # Setup command line parser
    parser = argparse.ArgumentParser( description="Lookup subjects or MR sessions in XNAT.")
    parser.add_argument('-c', '--config',
                        default=os.path.join( os.path.expanduser("~"), '.server_config/ncanda.cfg'),
                        help="Path to configuration file in pyxnat format.")
    parser.add_argument("-o", "--outfile",
                        help="Save output to csv file.")
    parser.add_argument("-p", "--print-project",
                        help="Print project name.", action="store_true")
    parser.add_argument("-r", "--reverse-lookup",
                        help="Lookup by REDCap ID.", action="store_true")
    parser.add_argument("-k", "--print-keys",
                        help="Print search keys in addition to search result.", action="store_true")
    parser.add_argument("-v", "--verbose",
                        help="Switch on verbose reporting", action="store_true")
    parser.add_argument("search",
                        help="String(s) to search for.", nargs='+')
    argv = parser.parse_args()
    verbose = argv.verbose
    sys.exit(main(args=argv))
