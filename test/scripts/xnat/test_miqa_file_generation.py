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

# import miqa_file_generation_ as miqa_file_generation
current_dir=os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, '../../../scripts/xnat'))
import miqa_file_generation
import upload_visual_qc

data_dir=os.path.join(current_dir,"data")

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
def test_read_write_json(file_prefix, sibis_session):
    # Read Json file
    file_name=file_prefix +".json"
    orig_file=os.path.join(data_dir,file_name)
    assert(os.path.exists(str(orig_file)))
    json_dict = miqa_file_generation.read_miqa_import_file(file_name, data_dir)

    # Write out Json File
    created_file=os.path.join("/tmp",file_name)
    if os.path.exists(created_file):
        os.remove(created_file)

    miqa_file_generation.write_miqa_import_file(json_dict, file_name, "/tmp")

    # Compare_File
    assert(filecmp.cmp(orig_file,created_file))


@pytest.mark.parametrize("file_prefix",
                         ["test_miqa_file_generation_bad"])
def test_read_bad_json(file_prefix, sibis_session):
    # Read Json file
    file_name= file_prefix +".json"
    orig_file=os.path.join(data_dir,file_name)
    assert(os.path.exists(str(orig_file)))
    json_dict = miqa_file_generation.read_miqa_import_file(file_name, data_dir)
    assert json_dict == {}, "Json dict should be empty bc read from bad file"


@pytest.mark.parametrize("file_prefix",
                        [
                            "test_miqa_file_generation_3"
                        ])

def test_json_convert_check_new_sessions(file_prefix):
    # Read Json file
    file_name=file_prefix +".json"
    orig_file=os.path.join(data_dir,file_name)
    assert(os.path.exists(str(orig_file)))
    json_dict = miqa_file_generation.read_miqa_import_file(file_name, data_dir)
    json_df: pd.DataFrame = miqa_file_generation.convert_json_to_check_new_sessions_df(json_dict)

    
@pytest.mark.parametrize("file_prefix",
                        [
                            "test_miqa_file_generation",
                            "test_miqa_file_generation_2"
                        ])

def test_json_convert_check_new_sessions_df(file_prefix):
    # Read Json file
    file_name=file_prefix +".json"
    orig_file=os.path.join(data_dir,file_name)
    assert(os.path.exists(str(orig_file)))
    json_dict = miqa_file_generation.read_miqa_import_file(file_name, data_dir)
    json_df: pd.DataFrame = miqa_file_generation.convert_json_to_check_new_sessions_df(json_dict)

    # Read legacy CSV file
    csv_file=os.path.join(data_dir,file_prefix + ".csv")
    csv_df: pd.DataFrame = upload_visual_qc.read_csf_file(csv_file)

    # sort so we are comparing similar thing
    dataframe_cols = csv_df.columns.to_list()
    json_df = json_df.sort_values(by=dataframe_cols).reset_index(drop=True)
    csv_df = csv_df.sort_values(by=dataframe_cols).reset_index(drop=True)

    df_diffs = csv_df.compare(json_df)
    assert len(df_diffs) == 0, "DataFrames should be identical."




@pytest.mark.parametrize("file_name",
                        [
                            "test_miqa_file_generation_write.json"
                        ])
def test_write_to_json_(file_name,project_list):


    #
    # Test 1: array created by check_new_scan cannot be written to json 
    #
    scans_to_qc = ['xnat_experiment_id,nifti_folder,scan_id,scan_type,experiment_note,decision,scan_note\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,2,ncanda-t2fse-v1,"",0,"UF(2022-09-01): uf UF(2022-09-01): this person&apos;s white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,3,ncanda-mprage-v1,"",0,"UF(2022-09-01): this person&apos;s white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,4,ncanda-dti6b500pepolar-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,6,ncanda-dti60b1000-v1,"",0,"UF(2022-09-01): this person&amp;apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,12,ncanda-dti30b400-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,18,ncanda-grefieldmap-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,19,ncanda-grefieldmap-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,20,ncanda-rsfmri-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11678,/fs/storage/XNAT/archive/ucsd_incoming/arc001/E-99999-P-9-20220831/RESOURCES/nifti,3,ncanda-t1spgr-v1,"",0,"MP(2022-09-16): Hole in the phantom"\n', 'NCANDA_E11718,/fs/storage/XNAT/archive/duke_incoming/arc001/C-00000-P-0-20220906/RESOURCES/nifti,3,ncanda-rsfmri-v1,"",0,"MP(2022-09-16): Damaged Phantom"\n', 'NCANDA_E11749,/fs/storage/XNAT/archive/duke_incoming/arc001/C-00000-P-0-20220912/RESOURCES/nifti,3,ncanda-rsfmri-v1,"",0,"UF(2022-09-22): damaged phantom"\n', 'NCANDA_E11782,/fs/storage/XNAT/archive/sri_incoming/arc001/B-00000-P-0-20221006/RESOURCES/nifti,3,ncanda-rsfmri-v1,"",0,"UF(2022-10-10): UF: damaged phantom"\n', 'NCANDA_E11788,/fs/storage/XNAT/archive/duke_incoming/arc001/C-00000-P-0-20221006/RESOURCES/nifti,3,ncanda-rsfmri-v1,"",0,"UF(2022-10-10): phantom damaged"\n']
    created_file=os.path.join("/tmp",file_name)
    if os.path.exists(created_file):
        os.remove(created_file)

    # write 
    successFlag = miqa_file_generation.write_miqa_import_file(scans_to_qc, file_name, "/tmp")
    assert successFlag == False, "Writing Json file should have failed bc it is not correct dictionary"

    #
    # Test 2: Turn into miqa dictionary 
    #
    subject_mapping = {'NCANDA_E11640': ('NCANDA_S00288', 'D-00155-M-0-20220818', 'ohsu_incoming'), 'NCANDA_E11663': ('NCANDA_S01175', 'D-00330-M-9-20220901', 'sri_incoming'), 'NCANDA_E11678': ('NCANDA_S00006', 'E-99999-P-9-20220831', 'ucsd_incoming'), 'NCANDA_E11718': ('NCANDA_S00026', 'C-00000-P-0-20220906', 'duke_incoming'), 'NCANDA_E11749': ('NCANDA_S00026', 'C-00000-P-0-20220912', 'duke_incoming'), 'NCANDA_E11778': ('NCANDA_S00906', 'B-80504-M-2-20220707', 'sri_incoming'), 'NCANDA_E11782': ('NCANDA_S00039', 'B-00000-P-0-20221006', 'sri_incoming'), 'NCANDA_E11788': ('NCANDA_S00026', 'C-00000-P-0-20221006', 'duke_incoming'), 'NCANDA_E11787': ('NCANDA_S01180', 'X-90001-M-1-20220928', 'ohsu_incoming'), 'NCANDA_E11794': ('NCANDA_S01181', 'X-90002-M-1-20220926', 'ohsu_incoming'), 'NCANDA_E11796': ('NCANDA_S00143', 'D-00092-F-2-20220924', 'ohsu_incoming'), 'NCANDA_E11798': ('NCANDA_S00017', 'D-99999-P-9-20220922', 'ohsu_incoming'), 'NCANDA_E11800': ('NCANDA_S00016', 'D-00000-P-0-20220922', 'ohsu_incoming'), 'NCANDA_E11806': ('NCANDA_S00016', 'D-00000-P-0-20221001', 'ohsu_incoming'), 'NCANDA_E11808': ('NCANDA_S00017', 'D-99999-P-9-20221001', 'ohsu_incoming'), 'NCANDA_E11810': ('NCANDA_S00184', 'D-00056-M-2-20221003', 'ohsu_incoming'), 'NCANDA_E11814': ('NCANDA_S00017', 'D-99999-P-9-20221007', 'ohsu_incoming'), 'NCANDA_E11816': ('NCANDA_S00016', 'D-00000-P-0-20221007', 'ohsu_incoming'), 'NCANDA_E11822': ('NCANDA_S01182', 'X-90004-F-1-20221001', 'ohsu_incoming'), 'NCANDA_E11826': ('NCANDA_S01183', 'X-90003-F-1-20221003', 'ohsu_incoming'), 'NCANDA_E11828': ('NCANDA_S01184', 'X-90005-F-1-20220927', 'ohsu_incoming'), 'NCANDA_E11833': ('NCANDA_S01002', 'B-00553-M-6-20221013', 'sri_incoming'), 'NCANDA_E11795': ('NCANDA_S01180', 'X-90001-M-1-20220928_legacy', 'ohsu_incoming'), 'NCANDA_E11797': ('NCANDA_S00289', 'D-00107-F-3-20221017', 'ohsu_incoming'), 'NCANDA_E11799': ('NCANDA_S00017', 'D-99999-P-9-20221014', 'ohsu_incoming'), 'NCANDA_E11803': ('NCANDA_S00720', 'D-00367-F-2-20221018', 'ohsu_incoming'), 'NCANDA_E11807': ('NCANDA_S00704', 'D-00342-M-0-20221012', 'ohsu_incoming'), 'NCANDA_E11811': ('NCANDA_S00017', 'D-99999-P-9-20221018', 'ohsu_incoming'), 'NCANDA_E11815': ('NCANDA_S00016', 'D-00000-P-0-20221018', 'ohsu_incoming'), 'NCANDA_E11819': ('NCANDA_S00016', 'D-00000-P-0-20221014', 'ohsu_incoming'), 'NCANDA_E11831': ('NCANDA_S01188', 'X-90008-M-1-20220826', 'ohsu_incoming'), 'NCANDA_E11838': ('NCANDA_S01187', 'X-90006-M-1-20221006', 'ohsu_incoming'), 'NCANDA_E11840': ('NCANDA_S01186', 'X-90007-M-1-20220929', 'ohsu_incoming'), 'NCANDA_E11842': ('NCANDA_S01188', 'X-90008-M-1-20220926', 'ohsu_incoming'), 'NCANDA_E11844': ('NCANDA_S01185', 'X-90009-F-1-20220928', 'ohsu_incoming'), 'NCANDA_E11859': ('NCANDA_S00411', 'E-00403-F-8-20221101', 'ucsd_incoming')}

    rows_cols = [row.replace('\n', '').split(',') for row in scans_to_qc]
    df = pd.DataFrame(rows_cols[1:], columns=rows_cols[0])    
    new_df = miqa_file_generation.convert_dataframe_to_new_format(df,None, subject_mapping)
    scans_to_qc_json_dict = miqa_file_generation.import_dataframe_to_dict(new_df,project_list)

    # Test that each project exists in dictionary
    for PRJ in project_list :
        assert PRJ in scans_to_qc_json_dict['projects'].keys(), "Could not find " + PRJ + "!"   

    #
    # Test 3: Write miqa dictionary to json file
    #
    successFlag = miqa_file_generation.write_miqa_import_file(scans_to_qc_json_dict, file_name, "/tmp", True)
    assert successFlag == True, "Writing Json file should have been successsfull "

    # os.remove(os.path.join("/tmp",file_name))

    
