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
import pandas as pd 
from unittest.mock import patch
import sibispy
from sibispy.tests.utils import get_session
current_dir=os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, '../../../scripts/xnat/'))
import miqa_file_generation_ as miqa_file_generation
import upload_visual_qc

sibis_session = sibispy.Session()
if not sibis_session.configure():
    print("Error: session configure file was not found")
    sys.exit()

project_list = ["DUKE", "OHSU", "SRI", "UCSD", "UPMC"]

def test_read_write(file_prefix="test_miqa_file_generation"):
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

    # Compare data of json with original csv
    csv_file=os.path.join(current_dir,file_prefix + ".csv")
    csv_df=upload_visual_qc.read_csf_file(csv_file)

    # does not work - only care about columns defined in csv_df.columns
    json_df=pd.DataFrame(json_dict.items()) 
    assert(json_df[csv_df.columns]==csv_df )
    
test_read_write()
test_read_write("test_miqa_file_generation_2")
