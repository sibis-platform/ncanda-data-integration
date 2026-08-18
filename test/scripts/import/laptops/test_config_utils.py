from __future__ import absolute_import

import os
import sys

import yaml

sys.path.append(os.path.join(os.path.dirname(__file__),
                             '../../../../scripts/import/laptops/'))
from config_utils import flatten_path_dict


def test_flatten_subdirs_and_lists():
    paths = {'ohsu':
                {'test': 'simple',
                 'pasat': [
                     'A-31',
                     'B-32',
                     {'example': ['C-20']}
                 ]}}
    assert sorted(flatten_path_dict(paths, '/import', delimiter='/')) == [
        '/import/ohsu/pasat/A-31',
        '/import/ohsu/pasat/B-32',
        '/import/ohsu/pasat/example/C-20',
        '/import/ohsu/test/simple',
    ]


def test_flatten_value_less_keys():
    paths = {'ohsu': {'pasat': {'A-31': None, 'B-32': None}}}
    assert sorted(flatten_path_dict(paths, '/import', delimiter='/')) == [
        '/import/ohsu/pasat/A-31',
        '/import/ohsu/pasat/B-32',
    ]


def test_flatten_value_less_keys_in_list():
    paths = {'ohsu': {'pasat': ['A-31', {'B-32': None}]}}
    assert sorted(flatten_path_dict(paths, '/import', delimiter='/')) == [
        '/import/ohsu/pasat/A-31',
        '/import/ohsu/pasat/B-32',
    ]


def test_flatten_yaml_merged_sets():
    # The shape special_cases.yml has to use to share one file list between
    # sites, since YAML cannot merge sequences
    settings = yaml.safe_load("""
    ignore_processed_paths:
      _shared: &SHARED
        ? E-01099-M-7-2017-09-19.csv
        ? E-01318-M-2-2017-08-28.csv
      ohsu:
        pasat:
          <<: *SHARED
          ? OHSU-specific-file.csv
      sri:
        pasat:
          <<: *SHARED
    """)
    flattened = flatten_path_dict(settings['ignore_processed_paths'],
                                  '/import', delimiter='/')
    for site in ['ohsu', 'sri']:
        assert '/import/{}/pasat/E-01099-M-7-2017-09-19.csv'.format(site) in flattened
        assert '/import/{}/pasat/E-01318-M-2-2017-08-28.csv'.format(site) in flattened
    assert '/import/ohsu/pasat/OHSU-specific-file.csv' in flattened
    assert '/import/sri/pasat/OHSU-specific-file.csv' not in flattened


def test_flatten_empty_dict():
    assert flatten_path_dict({}, '/import', delimiter='/') == []
