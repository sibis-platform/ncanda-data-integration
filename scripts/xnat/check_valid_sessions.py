#!/usr/bin/env python
"""
NCANDA Scan Usability Report

Validate the usability of NCANDA scans for a given visit
"""
__author__ = "Nolan Nichols <http://orcid.org/0000-0003-1099-3328>"
__modified__ = "2015-08-04"

import os
import glob
import json
import tempfile

import redcap
import requests
import pandas as pd
from lxml import etree

# Verbose setting for cli
verbose = None

# Define global namespace for parsing XNAT XML files
ns = {'xnat': 'http://nrg.wustl.edu/xnat'}

# Define global format to be used in XNAT requests
return_format = '?format=csv'

# Define global scan types for modalities
t1_scan_types = ['ncanda-t1spgr-v1', 'ncanda-mprage-v1']
t2_scan_types = ['ncanda-t2fse-v1']


def get_config(config_file):
    """
    Get a json configuration in pyXNAT format
    :param config_file: str
    :return: dict
    """
    path = os.path.abspath(config_file)
    with open(path, 'rb') as fi:
        config = json.load(fi)
    config.update(api=config['server'] + '/data')
    if verbose:
        print("Getting configurtion file: {0}".format(path))
    return config


def get_collections(config):
    """
    Get a dictionary of lambda functions that create collection URLs
    :param config: dict
    :return: dict
    """
    server = config['api']
    collections = dict(projects=lambda: server + '/projects',
                       subjects=lambda x: server + '/{0}/subjects'.format(x),
                       experiments=lambda: server + '/experiments')
    if verbose:
        print("Getting collections configuration...")
    return collections


def get_entities(config):
    """
    Get a dictionary of lambda functions that create entity URLs
    :param config: dict
    :return: dict
    """
    server = config['api']
    entities = dict(project=lambda x: server + '/projects/{0}'.format(x),
                    subject=lambda x: server + '/subjects/{0}'.format(x),
                    experiment=lambda x:
                    server + '/experiments/{0}'.format(x))
    if verbose:
        print("Getting entities configuration...")
    return entities


def get_xnat_session(config):
    """
    Get a requests.session instance from the config

    :return: requests.session
    """
    jsessionid = ''.join([config['api'], '/JSESSIONID'])
    session = requests.session()
    session.auth = (config['user'], config['password'])
    session.get(jsessionid)
    if verbose:
        print("Getting an XNAT session using: {0}".format(jsessionid))
    return session


def write_experiments(config, session):
    """
    Write out a csv file representing all the experiments in the given XNAT
    session.

    :param config: dict
    :param session: requests.session
    :return: str
    """
    experiments_filename = tempfile.mktemp()
    collections = get_collections(config)
    experiments = session.get(collections.get('experiments')() + return_format)
    with open(experiments_filename, 'w') as fi:
        fi.flush()
        fi.write(experiments.text)
        fi.close()
    if verbose:
        print("Writing list of experiment ids to temp: {0}".format(experiments_filename))
    return experiments_filename


def extract_experiment_xml(config, session, experiment_dir, extract=None):
    """
    Open an experiments csv file, then extract the XML representation,
    and write it to disk.

    :param config: dict
    :param session: requests.session
    :param experiment_dir: str
    :param extract: int
    :return: str
    """
    entities = get_entities(config)
    experiments_file = write_experiments(config, session)
    # make sure the output directory exists and is empty
    outdir = os.path.abspath(experiment_dir)
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    else:
        [os.remove(f) for f in glob.glob(os.path.join(outdir, '*'))]
    df_experiments = pd.read_csv(experiments_file)
    if not extract:
        if verbose:
            print("Running XML extraction for all sessions: {0} Total".format(df_experiments.shape[0]))
        extract = df_experiments.shape[0]
    experiment_ids = df_experiments.ID[:extract]
    experiment_files = list()
    for idx, experiment_id in experiment_ids.iteritems():
        experiment = session.get(entities.get('experiment')(experiment_id) + return_format)
        experiment_file = os.path.join(outdir, '{0}.xml'.format(experiment_id))
        experiment_files.append(experiment_file)
        with open(experiment_file, 'w') as fi:
            fi.flush()
            fi.write(experiment.text)
            fi.close()
        if verbose:
            num = idx + 1
            print("Writing XML file {0} of {1} to: {2}".format(num, extract, experiment_file))
    return experiment_files


def get_experiment_info(experiment_xml_file):
    """
    Extract basic information from the experiment xml file and return a
    dictionary

    :param experiment_xml_file: str
    :return: dict
    """
    xml = etree.parse(experiment_xml_file)
    root = xml.getroot()

    site_experiment_id = root.attrib.get('label')
    site_id = site_experiment_id[0:11]
    site_experiment_date = site_experiment_id[12:20]

    project = root.attrib.get('project')
    experiment_id = root.attrib.get('ID')
    experiment_date = root.find('./xnat:date', namespaces=ns).text

    subject_id = root.find('./xnat:subject_ID', namespaces=ns).text
    result = dict(site_id=site_id,
                  subject_id=subject_id,
                  site_experiment_id=site_experiment_id,
                  site_experiment_date=site_experiment_date,
                  project=project,
                  experiment_id=experiment_id,
                  experiment_date=experiment_date)
    if verbose:
        print("Parsed experiment info for: {0}".format(result))
    return result


def get_experiments_dir_info(experiments_dir):
    """
    Get a list of experiment dicts from all the experiment xml files in the
    experiments directory

    :param experiments_dir: str
    :return: list
    """
    results = list()
    if os.path.exists(os.path.abspath(experiments_dir)):
        glob_path = ''.join([os.path.abspath(experiments_dir), '/*'])
        experiment_files = glob.glob(glob_path)
    else:
        experiment_files = list()
    for path in experiment_files:
        results.append(get_experiment_info(path))
    return results


def get_scans_info(experiment_xml_file):
    """
    Get a dict of dicts for each scan from an XNAT experiment XML document

    :param experiment_xml_file: lxml.etree.Element
    :return: list
    """
    xml = etree.parse(experiment_xml_file)
    root = xml.getroot()
    experiment_id = root.attrib.get('ID')
    result = list()
    scans = root.findall('./xnat:scans/xnat:scan', namespaces=ns)
    for scan in scans:
        values = dict()
        scan_id = scan.attrib.get('ID')
        scan_type = scan.attrib.get('type')
        # handle null finds
        values.update(quality=scan.find('./xnat:quality', namespaces=ns))
        values.update(series_description=scan.find(
            './xnat:series_description', namespaces=ns))
        values.update(coil=scan.find('./xnat:coil', namespaces=ns))
        values.update(field_strength=scan.find('./xnat:fieldStrength',
                                               namespaces=ns))
        for k, v in values.iteritems():
            try:
                values[k] = v.text
            except AttributeError, e:
                values[k] = None
                if verbose:
                    print(e, "for attribute {0} in scan {1} of experiment {2}".format(k, scan_id, experiment_id))
        scan_dict = dict(experiment_id=experiment_id,
                         scan_id=scan_id,
                         scan_type=scan_type,
                         quality=values.get('quality'),
                         series_description=values.get('series_description'),
                         coil=values.get('coil'),
                         field_strength=values.get('field_strength'))
        result.append(scan_dict)
    return result


def get_reading_info(experiment_xml_file):
    """
    Get a dict of dicts for each reading from an XNAT experiment XML document

    :param experiment_xml_file: lxml.etree.Element
    :return: list
    """
    xml = etree.parse(experiment_xml_file)
    root = xml.getroot()
    experiment_id = root.attrib.get('ID')
    try:
        note = root.find('./xnat:note', namespaces=ns).text
    except AttributeError:
        note = None
        pass
    result = dict(experiment_id=experiment_id,
                  note=note,
                  datetodvd=None,
                  findings=None,
                  findingsdate=None,
                  excludefromanalysis=None,
                  physioproblemoverride=None,
                  dtimismatchoverride=None,
                  phantommissingoverride=None)
    values = dict()
    fields = root.findall('./xnat:fields/xnat:field', namespaces=ns)
    for field in fields:
        name = field.attrib.get('name')
        value = root.xpath('.//xnat:field[@name="{0}"]/text()'.format(name),
                           namespaces=ns)
        # handle null finds
        values[name] = value
    for k, v in values.iteritems():
        try:
            values[k] = v[1]
        except IndexError:
            values[k] = None
    result.update(values)
    return result


def get_experiments_dir_reading_info(experiments_dir):
    """
    Get a list of reading dicts from all the experiment xml files in the
    experiments directory

    :param experiments_dir: str
    :return: list
    """
    results = list()
    if os.path.exists(os.path.abspath(experiments_dir)):
        glob_path = ''.join([os.path.abspath(experiments_dir), '/*'])
        experiment_files = glob.glob(glob_path)
    else:
        experiment_files = list()
    for path in experiment_files:
        results.append(get_reading_info(path))
    return results


def get_experiments_dir_scan_info(experiments_dir):
    """
    Get a list of scan dicts from all the experiment xml files in the
    experiments directory

    :param experiments_dir: str
    :return: list
    """
    results = list()
    if os.path.exists(os.path.abspath(experiments_dir)):
        glob_path = ''.join([os.path.abspath(experiments_dir), '/*'])
        experiment_files = glob.glob(glob_path)
    else:
        experiment_files = list()
    for path in experiment_files:
        results.append(get_scans_info(path))
    return results


def get_scans_by_type(scans, scan_type):
    """
    Get scans based on their type

    :param scans: dict
    :param scan_type: str
    :return:
    """
    result = list()
    for scan in scans:
        if scan['scan_type'] == scan_type:
            result.append(scan)
    return result


def scans_to_dataframe(scans):
    """
    Convert scan dict to a pandas.DataFrame

    :param scans: dict
    :return: pandas.DataFrame
    """
    flat = [item for sublist in scans for item in sublist]
    return pd.DataFrame(flat)


def experiments_to_dataframe(experiments):
    """
    Convert a list of experiment dicts to a pandas.DataFrame

    :param experiments: dict
    :return: pandas.DataFrame
    """
    return pd.DataFrame(experiments)


def reading_to_dataframe(reading):
    """
    Convert a list of reading dicts to a pandas.DataFrame

    :param reading: dict
    :return: pandas.DataFrame
    """
    return pd.DataFrame(reading)


def merge_experiments_scans_reading(experiments, scans, reading):
    """
    Merge an experiments dataframe with a scan dataframe

    :param experiments: dict
    :param scans: dict
    :return: pandas.DataFrame
    """
    experiments_df = experiments_to_dataframe(experiments)
    scans_df = scans_to_dataframe(scans)
    reading_df = reading_to_dataframe(reading)
    exp_scan = pd.merge(experiments_df, scans_df, how='inner')
    merged = pd.merge(exp_scan, reading_df, how='inner')
    # reindex using multi-index of subject, experiment, scan
    result = merged.to_records(index=False)
    idx = pd.MultiIndex.from_arrays([merged.subject_id.values,
                                     merged.experiment_id.values,
                                     merged.scan_id.values],
                                    names=['subject_id',
                                           'experiment_id',
                                           'scan_id'])
    return pd.DataFrame(result, index=idx)


def main(args=None):
    if args.update:
        config = get_config(args.config)
        session = get_xnat_session(config)
        extract_experiment_xml(config, session,
                               args.experimentsdir, args.num_extract)

    # extract info from the experiment XML files
    experiment = get_experiments_dir_info(args.experimentsdir)
    scan = get_experiments_dir_scan_info(args.experimentsdir)
    reading = get_experiments_dir_reading_info(args.experimentsdir)
    df = merge_experiments_scans_reading(experiment, scan, reading)

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

        # Find window for 1 year follow-up
        followup_yr1_min = baseline_df.experiment_date + pd.datetools.Day(n=270)
        followup_yr1_max = baseline_df.experiment_date + pd.datetools.Day(n=450)

        followup_yr1_df = subject_df[(subject_df.experiment_date > followup_yr1_min[0]) &
                                     (subject_df.experiment_date < followup_yr1_max[0])]

        # filter for specific scan types
        t1_df = followup_yr1_df[followup_yr1_df.scan_type.isin(t1_scan_types)]
        t2_df = followup_yr1_df[followup_yr1_df.scan_type.isin(t2_scan_types)]

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

    parser = argparse.ArgumentParser(prog='ncanda_t1_t2_baseline_usability.py',
                                     description=__doc__)
    parser.add_argument('-c', '--config',
                        type=str,
                        default=os.path.join(os.path.expanduser('~'),
                                             '.server_config', 'ncanda.cfg'))
    parser.add_argument('-e', '--experimentsdir',
                        type=str,
                        default='/tmp/experiments',
                        help='Name of experiments xml directory')
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

    sys.exit(main(args=argv))
