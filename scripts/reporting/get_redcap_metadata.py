import sibispy
from sibispy import sibislogger as slog
import sys
import pandas as pd
import numpy as np

import argparse


def export_datadict(api, filename):
    return api.export_metadata(format='df').to_csv(filename)


def export_fem(api, filename):
    return api.export_fem(format='df').to_csv(filename)


def main(args):
    # 1. Set up API connection with sibispy
    slog.init_log(args.verbose, False,
                  'Download Redcap data dictionary and form-event mapping',
                  'get_redcap_metadata', None)
    slog.startTimer1()

    # Set up Redcap
    session = sibispy.Session()
    if not session.configure(ordered_config_load_flag=True):
        if args.verbose:
            print "Error: session configure file was not found"
        sys.exit()

    redcap_api = session.connect_server(args.project, True)
    if not redcap_api:
        if args.verbose:
            print "Error: Couldn't connect to Redcap %s project" % args.project
        sys.exit()

    if args.datadict:
        return export_datadict(redcap_api, args.datadict)
    if args.fem:
        return export_fem(redcap_api, args.fem)


if __name__ == '__main__':
    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'

    parser = argparse.ArgumentParser(prog="get_redcap_metadata.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument("-v", "--verbose",
                        help="Verbose operation",
                        action="store_true")
    parser.add_argument('-p', '--project',
                        help="Redcap project that you want the metadata of",
                        choices=["data_entry", "import_laptops"])

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--fem', action='store',
                       help="Name of CSV file in which to save the form-event mapping",
                       type=argparse.FileType('w'))
    group.add_argument('--datadict',
                       help="Name of CSV file in which to save the datadict",
                       action='store',
                       type=argparse.FileType('w'))

    parsed_args = parser.parse_args()
    sys.exit(main(args=parsed_args))
