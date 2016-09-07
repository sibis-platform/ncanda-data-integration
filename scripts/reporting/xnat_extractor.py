#!/usr/bin/env python
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
NCANDA XNAT Extractor

Extract all experiment, scan, and reading data from NCANDA's XNAT server.
"""
__author__ = "Nolan Nichols <http://orcid.org/0000-0003-1099-3328>"
__modified__ = "2015-08-26"

import os
import glob
import json
import tempfile

import requests
import pandas as pd
from lxml import etree

# Verbose setting for cli
verbose = None

# Define global namespace for parsing XNAT XML files
ns = {'xnat': 'http://nrg.wustl.edu/xnat'}

# Define global format to be used in XNAT requests
return_format = '?format=csv'


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
        print("Getting configuration file: {0}".format(path))
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
    try : 
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
    except : 
        print "ERROR: %s does not have xnat:date or xnat:subject_ID defined !" % (experiment_xml_file)
        result = ""

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
        values.update(scan_note=scan.find('./xnat:note', namespaces=ns))

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
                         scan_note=values.get('scan_note'),
                         series_description=values.get('series_description'),
                         coil=values.get('coil'),
                         field_strength=values.get('field_strength'))
        result.append(scan_dict)
    return result


def get_reading_info(experiment_xml_file):
    """
    Get a dict of dicts for each reading from an XNAT experiment XML document
    These are the visit specific information, e.g. DateToDVD, Subject ID , session notes, ....  
    (no individual scan info) 

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
