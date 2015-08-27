#!/usr/bin/env python
"""
Neuroradiology Findings

Script to sync and generate reports on findings from radiology readings
"""
__author__ = 'Nolan Nichols <https://orcid.org/0000-0003-1099-3328>'
__modified__ = "2015-08-26"
import os

import pandas as pd

import xnat_extractor as xe

verbose = None


def set_experiment_attrs(config, project, subject, experiment, key, value):
    """
    Set the field for an MRSession

    For example, datetodvd, findingsdate, findings
    :param config:
    :param project:
    :param subject:
    :param experiment:
    :param key:
    :param value:
    :return:
    """
    config = xe.get_config(config)
    session = xe.get_xnat_session(config)
    api = config.get('api')
    path = '{}/projects/{}/subjects/{}/experiments/{}'.format(api, project, subject, experiment)
    xsi = 'xnat:mrSessionData'
    field = 'xnat:mrSessionData/fields/field[name={}]/field'.format(key)
    payload = {'xsiType': xsi, field: value}
    return session.put(path, params=payload)


def update_findings_date(config, merged_findings):
    """
    For all records found, set the findings date attribute to datatodvd

    :param config: dict
    :param merged_findings: pd.DataFrame
    :return:
    """
    for idx, row in merged_findings.iterrows():
        result = set_experiment_attrs(config, row.project, row.subject_id, row.experiment_id, 'findingsdate', row.datetodvd)
        if verbose:
            print("Updated experiment: {}").format(result)
    return


def findings_date_empty(reading):
    """
    Find all experiments that have a finding recorded but no date entered.

    :param reading: list of dicts
    :return: pd.DataFrame
    """
    df = xe.reading_to_dataframe(reading)
    has_finding = df[~df.findings.isnull()]
    no_findings_date = has_finding[has_finding.findingsdate.isnull()]
    return no_findings_date


def inner_join_dataframes(df1, df2):
    """
    Join two dataframes using an inner join

    :param df1:
    :param df2:
    :return:
    """
    return pd.merge(df1, df2, how='inner')


def main(args=None):
    if args.update:
        config = xe.get_config(args.config)
        session = xe.get_xnat_session(config)
        xe.extract_experiment_xml(config, session,
                                  args.experimentsdir, args.num_extract)

    # extract info from the experiment XML files
    experiment = xe.get_experiments_dir_info(args.experimentsdir)
    reading = xe.get_experiments_dir_reading_info(args.experimentsdir)
    experiment_df = xe.experiments_to_dataframe(experiment)
    no_findings_date = findings_date_empty(reading)
    merged_findings = inner_join_dataframes(experiment_df, no_findings_date)
    if args.findings:
        update_findings_date(args.config, merged_findings)


if __name__ == "__main__":
    import sys
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="neurorad_findings.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('-c', '--config',
                        type=str,
                        default=os.path.join(os.path.expanduser('~'),
                                             '.server_config', 'ncanda.cfg'))
    parser.add_argument('-e', '--experimentsdir',
                        type=str,
                        default='/tmp/experiments',
                        help='Name of experiments xml directory')
    parser.add_argument('-f', '--findings',
                        type=str,
                        action='store_true',
                        help='If findings are reported and the findings date is None then set it to the date of dvd.')
    parser.add_argument('-o', '--outfile',
                        type=str,
                        default='/tmp/neurorad_findings.csv',
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
