#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Neuroradiology Findings

Script to sync and generate reports on findings from radiology readings

Examples
========
- Findings and Findings Date is empty before a given date
python neurorad_findings.py --update --report-type no_findings_before_date --before-date 2015-06-08

Report Types
===========
no_findings_date - no findings date is listed but there is a finding
no_findings - no finding but a finding date is listed
no_findings_or_date - no findings or findings date listed
no_findings_before_date - filters no_findings_or_date by date

"""

import os
import sys
import pandas as pd

import sibispy
from sibispy import sibislogger as slog

import xnat_extractor as xe

verbose = None

def set_experiment_attrs(session,server,project, subject, experiment, key, value):
        """
        Set the field for an MRSession

        For example, datetodvd, findingsdate, findings
        :param config: str
        :param project: str
        :param subject: str
        :param experiment: str
        :param key: str
        :param value: str
        :return: str
        """
        print "ERROR: NEVER TESTED IT - PLEASE DO SO BEFORE USE" 
        sys.exit()

        server_path = session.get_xnat_data_address() 
        path = '{}/projects/{}/subjects/{}/experiments/{}'.format(server_path, project, subject, experiment)
        xsi = 'xnat:mrSessionData'
        field = 'xnat:mrSessionData/fields/field[name={}]/field'.format(key)
        payload = {'xsiType': xsi, field: value}

        return server.put(path, params=payload)


def update_findings_date(session, server, merged_findings):
    """
    For all records found, set the findings date attribute to datatodvd

    :param merged_findings: pd.DataFrame
    :return:
    """
    for idx, row in merged_findings.iterrows():
        result = set_experiment_attrs(session,server,row.project, row.subject_id, row.experiment_id, 'findingsdate', row.datetodvd)
        if verbose:
            print("Updated experiment: {}".format(result))
    return


def findings_date_empty(df):
    """
    Find all experiments that have a finding recorded but no date entered.

    :param df: pd.DataFrame
    :return: pd.DataFrame
    """
    has_finding = df[~df.findings.isnull()]
    no_findings_date = has_finding[has_finding.findingsdate.isnull()]
    return no_findings_date


def findings_empty(df):
    """
    Find all experiments that have a finding date recorded but no finding entered.

    :param df: pd.DataFrame
    :return: pd.DataFrame
    """
    has_findings_date = df[~df.findingsdate.isnull()]
    no_findings_date = has_findings_date[has_findings_date.findings.isnull()]
    return no_findings_date


def findings_and_date_empty(df):
    """
    Find all experiments that have empty findings date and findings.

    :param df: pd.DataFrame
    :return: pd.DataFrame
    """
    no_findings_or_date = df[(df.findings.isnull()) & (df.findingsdate.isnull())]
    return no_findings_or_date


def check_dvdtodate_before_date(df, before_date=None):
    """
    Find all experiments that have a datetodvd before a given date.
    Also convert date from string to datetime (YYYY-MM-DD)

    :param df: pd.DataFrame
    :return: pd.DataFrame
    """
    has_datetodvd = df[~df.datetodvd.isnull()]
    has_datetodvd.loc[:, 'datetodvd'] = has_datetodvd.datetodvd.astype('datetime64')
    date = pd.Timestamp(before_date)
    # date = pd.to_datetime(before_date)

    return has_datetodvd[has_datetodvd.datetodvd < date]


def inner_join_dataframes(df1, df2):
    """
    Join two dataframes using an inner join

    :param df1: pd.DataFrame
    :param df2: pd.DataFrame
    :return: pd.DataFrame
    """
    return pd.merge(df1, df2, how='inner')


def main(args=None):
    slog.init_log(False, False,'neurorad_findings', 'neurorad_findings',None)
    session = sibispy.Session()
    session.configure()
    if not session.configure() :
        if args.verbose:
            print "Error: session configure file was not found"
        sys.exit()

    server = session.connect_server('xnat_http', True)
    if not server:
        print "Error: could not connect to xnat server!" 
        sys.exit()

    # Update the cache of XNAT Experiment XML files
    if args.update:
        xe.extract_experiment_xml(session,args.experimentsdir, args.num_extract)

    # extract info from the experiment XML files
    experiment = xe.get_experiments_dir_info(args.experimentsdir)
    experiment_df = xe.experiments_to_dataframe(experiment)
    reading = xe.get_experiments_dir_reading_info(args.experimentsdir)
    reading_df = xe.reading_to_dataframe(reading)
    experiment_reading = inner_join_dataframes(experiment_df, reading_df)

    # exclude phantoms, but include the traveling human phantoms
    site_id_pattern = '[A-EX]-[0-9]{5}-[MFT]-[0-9]'
    df = experiment_reading[experiment_reading.site_id.str.contains(site_id_pattern)]

    result = None
    if args.report_type == 'no_findings_date':
        # Findings are listed without a findings date
        result = findings_date_empty(df)
        if args.set_findings_date:
            # Update the findings date to equal the date to dvd
            update_findings_date(session,server, result)

    elif args.report_type == 'no_findings':
        # Findings is empty but a date is listed
        result = findings_empty(df)

    elif args.report_type == 'no_findings_or_date':
        # Both the findings and findings date are empty
        result = findings_and_date_empty(df)
        if args.reset_datetodvd:
            record = result[result.experiment_id == experiment]
            project = record.project.values[0]
            subject = record.subject_id.values[0]
            experiment = args.reset_datetodvd
            set_experiment_attrs(session,server,project, subject, experiment, 'datetodvd', 'none')

    elif args.report_type == 'correct_dvd_date':
        dates_df = pd.read_csv(args.file_to_reset_datetodvd)
        result = pd.DataFrame(index=['Subject'], columns=['project', 'subject_id', 'experiment_id',
                 'site_experiment_id', 'datetodvd', 'findingsdate'])
        result = result.fillna(0)
        for subject in df['subject_id'].tolist():
            if subject in dates_df['mri_xnat_sid'].tolist():
                if args.verbose:
                    print "Checking for {}".format(subject)
                eids = dates_df[dates_df['mri_xnat_sid'] == subject]['mri_xnat_eids'].tolist()
                date = dates_df[dates_df['mri_xnat_sid'] == subject]['mri_datetodvd'].tolist()
                if eids != []:
                    if len(eids[0]) == 13:
                        experiment = eids[0]
                        record = df[df.experiment_id == experiment]
                        record_date = record['datetodvd'].tolist()
                        if date != [] and record_date != []:
                            if record_date[0] != date[0] or type(record_date[0]) != str() :
                                project = record.project.values[0]
                                subject = record.subject_id.values[0]
                                experiment = record.experiment_id.values[0]
                                set_experiment_attrs(session,server,project, subject, experiment, 'datetodvd', date[0])
                    elif len(eids[0]) == 27 or eids == None:
                        experiment = eids[0].split(" ")
                        for e in experiment:
                            record_date = record['datetodvd'].tolist()
                            record = df[df.experiment_id == e]
                            if date != [] and record_date != []:
                                if record_date[0] != date[0] or type(record_date[0]) == str():
                                    project = record.project.values[0]
                                    subject = record.subject_id.values[0]
                                    set_experiment_attrs(session,server,project, subject, e, 'datetodvd', date[0])

    elif args.report_type == 'no_findings_before_date':
        # Findings and Findings Date is empty before a given date
        if not args.before_date:
            raise(Exception("Please set --before-date YYYY-MM-DD when running the no_findings_before_date report."))
        has_dvd_before_date = check_dvdtodate_before_date(df, before_date=args.before_date)
        result = findings_and_date_empty(has_dvd_before_date)
        result.to_csv(args.outfile, index=False)
    else:
        raise(NotImplementedError("The report you entered is not in the list."))

    result.to_csv(args.outfile,
                  columns=['project', 'subject_id', 'experiment_id',
                           'site_experiment_id', 'datetodvd', 'findingsdate'],
                  index=False)
    if verbose:
        pd.set_option('display.max_rows', len(result))
        print("Total records found: {}".format(len(result)))
        print(result[['experiment_id', 'site_experiment_id']])
        pd.reset_option('display.max_rows')
        print("Finished!")

if __name__ == "__main__":
    import sys
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="neurorad_findings.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('-b', '--before-date',
                        type=str,
                        help='To be used with --report_type no_findings_before_date. YYYY-MM-DD')
    parser.add_argument('-c', '--config',
                        type=str,
                        default=os.path.join(os.path.expanduser('~'),
                                             '.server_config', 'ncanda.cfg'))
    parser.add_argument('-d', '--reset_datetodvd',
                        help='Reset the datetodvd to None for a given XNAT experiment id (e.g., NCANDA_E12345)')
    parser.add_argument('-e', '--experimentsdir',
                        type=str,
                        default='/tmp/experiments',
                        help='Name of experiments xml directory')
    parser.add_argument('-f', '--file_to_reset_datetodvd',
                        action='store',
                        help='CSV file used to reset the datetodvd to a specific date for a given XNAT experiment id (e.g., NCANDA_E12345)')
    parser.add_argument('-o', '--outfile',
                        type=str,
                        default='/tmp/neurorad_findings.csv',
                        help='Name of csv file to write.')
    parser.add_argument('-n', '--num-extract',
                        type=int,
                        help='Number of sessions to extract')
    parser.add_argument('-r', '--report-type',
                        type=str,
                        required=True,
                        choices=['no_findings_date', 'no_findings', 'no_findings_or_date', 'no_findings_before_date','correct_dvd_date'],
                        help='Select a report type. Note that no_findings_before_date requires --before_date.')
    parser.add_argument('-s', '--set-findings-date',
                        action='store_true',
                        help='If findings are reported and the findings date is None then set it to the date of dvd.')
    parser.add_argument('-u', '--update',
                        action='store_true',
                        help='Update the cache of xml files')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Print verbose output.')

    argv = parser.parse_args()

    verbose = argv.verbose
    #xe.verbose = argv.verbose
    sys.exit(main(args=argv))
