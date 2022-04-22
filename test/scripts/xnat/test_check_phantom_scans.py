#!/usr/bin/env python

##
##  Copyright 2017 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms
##

from __future__ import print_function
from builtins import next
import os
import sys
import glob
import pytest
from unittest.mock import patch
import sibispy
from sibispy.tests.utils import get_session
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../scripts/xnat/'))
import check_phantom_scans


@pytest.fixture
def session(config_file):
    return get_session(config_file)

@pytest.fixture
def email_adr(session):
    return session.get_email()

@pytest.fixture
def slog():
    '''
    Return a sibislogger instance initialized for a test session.
    '''
    from sibispy import sibislogger as slog
    timeLogFile = '/tmp/test_session-time_log.csv'
    if os.path.isfile(timeLogFile) : 
        os.remove(timeLogFile) 

    slog.init_log(False, False,'test_session', 'test_session','/tmp')
    return slog


def test_select_experiments(session, slog, email_adr):
    project = 'xnat'
    ifc = session.connect_server(project, True)
    def experiments_502(experiment_type, constraints):
        from .xnat.exceptions import XNATResponseError
        raise XNATResponseError('Invalid response from XNATSession for url {} (status {}):\n{}'.format('test_uri', 502, "test_text"))

    args = {'verbose': True}
    
    with patch.object(ifc.array, 'experiments', new=experiments_502):

        eid = "NCANDA_E00067"
        try:
            experiment = ifc.select.experiments[eid]
        except KeyError as e:
            pass

        sibis_config = session.get_operations_dir()
        assert(sibis_config, "Could not get operations directory from session")
        assert(not check_phantom_scans.check_experiment(session, ifc, sibis_config, args, email_adr, eid, experiment))
        
