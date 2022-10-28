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
                            # "test_miqa_file_generation_2"
                        ])
def test_json_convert_xnat_df(file_prefix):
    # Read Json file
    file_name=file_prefix +".json"
    orig_file=os.path.join(current_dir,file_name)
    assert(os.path.exists(str(orig_file)))    
    json_dict=miqa_file_generation.read_miqa_import_file(file_name,current_dir, False, miqa_file_generation.MIQAFileFormat.JSON)
    json_df: pd.DataFrame = miqa_file_generation.convert_json_to_xnat_dataframe(json_dict)

    # Read Legacy CSV file
    csv_file=os.path.join(current_dir,file_prefix + ".csv")
    csv_df: pd.DataFrame = upload_visual_qc.read_csf_file(csv_file)
    
    # sort so we are comparing similar thing
    dataframe_cols = ['xnat_experiment_id','scan_id','scan_type','nifti_folder','experiment_note','decision','scan_note']
    json_df = json_df.sort_values(by=dataframe_cols).reset_index(drop=True)
    csv_df = csv_df.sort_values(by=dataframe_cols).reset_index(drop=True)
    
    df_diffs = csv_df.compare(json_df)
    assert len(df_diffs) == 0, "DataFrames should be identical."


def get_site_from_folder(nifti_folder:str, prefix:str = "/fs/storage/XNAT/archive/"):
    site = nifti_folder.replace(prefix, "", 1)
    site = re.sub(r"_incoming/.*$", r"", site)
    return site.upper()

@pytest.mark.parametrize("file_prefix",
                         ["test_miqa_file_generation",
                          "test_miqa_file_generation_2"])
def test_json_has_csv_data(file_prefix, sibis_session, project_list):
    # Read Json file
    file_name=file_prefix +".json"
    orig_file=os.path.join(current_dir,file_name)
    assert(os.path.exists(str(orig_file)))    
    json_dict=miqa_file_generation. read_miqa_import_file(file_name,current_dir, False, miqa_file_generation.MIQAFileFormat.JSON)
    
    
    # Compare data of json with original csv
    csv_file=os.path.join(current_dir,file_prefix + ".csv")
    csv_df=upload_visual_qc.read_csf_file(csv_file)

    ## extract the site from the CSV data so we can index into JSON
    csv_df["_site"] = csv_df["nifti_folder"].apply(lambda x : get_site_from_folder(x) )

    for idx, scan in csv_df.iterrows():
        ## try fetching the JSON object using index coordinates from the csv file
        try:
            js_expt = json_dict["projects"][scan['_site']]["experiments"][scan["xnat_experiment_id"]]
            js_scan = js_expt["scans"][f"{scan['scan_id']}_{scan['scan_type']}"]
        except:
            ## If this fails, means the JSON data doesn't match CSV
            assert False, "should have found the scan."
        
        ## Validate that scan parameters
        assert js_scan["type"] == scan["scan_type"]
        if pd.isna(scan["decision"]):
            assert js_scan["last_decision"] == None
        else:
            assert js_scan["last_decision"]["decision"] == miqa_file_generation.MIQADecisionCodes[str(scan["decision"])]
            assert js_scan["last_decision"]["note"] == scan["scan_note"] or (pd.isna(scan["scan_note"]) and js_scan["last_decision"]["note"] in [None, ""])

        ## Not sure if this is the right comparison
        assert js_expt["notes"] == scan["experiment_note"] or (pd.isna(scan["experiment_note"]) and js_expt["notes"] in [None, ""])
        

