#!/usr/bin/env python

##
##  Copyright 2017 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms
##

from __future__ import print_function
from builtins import next
import os
import sys
import filecmp
import glob
import re
from tabnanny import verbose
import pandas as pd 
from unittest.mock import patch
import pytest
import sibispy
from sibispy.tests.utils import get_session
current_dir=os.path.dirname(__file__)
# sys.path.append(os.path.join(current_dir, '../../../'))
sys.path.append(os.path.join(current_dir, '../../../scripts/xnat'))
# import miqa_file_generation_ as miqa_file_generation
import miqa_file_generation
import upload_visual_qc


@pytest.fixture
def project_list():
    return ["DUKE", "OHSU", "SRI", "UCSD", "UPMC"]


@pytest.fixture
def sibis_session():
    sibispy.sibislogger.init_log(verbose=True)

    sibis_session = sibispy.Session()
    if not sibis_session.configure():
        print("Error: session configure file was not found")
        sys.exit()
    
    return sibis_session

@pytest.mark.parametrize("file_prefix",
                         ["test_miqa_file_generation",
                          "test_miqa_file_generation_2"])
def test_read_write_json(file_prefix, sibis_session, project_list):
    # Read Json file
    file_name=file_prefix +".json"
    orig_file=os.path.join(current_dir,file_name)
    assert(os.path.exists(str(orig_file)))    
    json_dict=miqa_file_generation. read_miqa_import_file(file_name,current_dir, False, miqa_file_generation.MIQAFileFormat.JSON)

    # Write out Json File
    created_file=os.path.join("/tmp",file_name)
    if os.path.exists(created_file):
        os.remove(created_file)
        
    miqa_file_generation.write_miqa_import_file(json_dict,file_name,"/tmp",False, format=miqa_file_generation.MIQAFileFormat.JSON,session=sibis_session,project_list=project_list)
     
    # Compare_File
    print(orig_file,created_file)
    assert(filecmp.cmp(orig_file,created_file))


@pytest.mark.parametrize("file_prefix",
                        [
                            "test_miqa_file_generation",
                            "test_miqa_file_generation_2"
                        ])
def test_json_convert_check_new_sessions_df(file_prefix):
    # Read Json file
    file_name=file_prefix +".json"
    orig_file=os.path.join(current_dir,file_name)
    assert(os.path.exists(str(orig_file)))    
    json_dict=miqa_file_generation.read_miqa_import_file(file_name,current_dir, False, miqa_file_generation.MIQAFileFormat.JSON)
    json_df: pd.DataFrame = miqa_file_generation.convert_json_to_check_new_sessions_df(json_dict)

    # Read Legacy CSV file
    csv_file=os.path.join(current_dir,file_prefix + ".csv")
    csv_df: pd.DataFrame = upload_visual_qc.read_csf_file(csv_file)
    
    # sort so we are comparing similar thing
    dataframe_cols = csv_df.columns.to_list()
    json_df = json_df.sort_values(by=dataframe_cols).reset_index(drop=True)
    csv_df = csv_df.sort_values(by=dataframe_cols).reset_index(drop=True)
    
    df_diffs = csv_df.compare(json_df)
    assert len(df_diffs) == 0, "DataFrames should be identical."




