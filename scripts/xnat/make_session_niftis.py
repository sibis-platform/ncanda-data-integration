#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
from __future__ import print_function
from builtins import str
import os
import glob
import shutil
import zipfile
import tempfile
import numpy
import re
import time 
import sys 
import datetime

import sibispy
from sibispy import sibislogger as slog
from sibispy import utils as sutils
from sibispy.xnat_util import XNATSessionElementUtil, XNATResourceUtil, XNATExperimentUtil

#
# Export experiment files to NIFTI
# Note only checks ones scanPtr as t2w only has one ! 
def dcm2niftiWithCheck(dcmDirList, niftiPrefix, project,eid, scanPtr, logFileFlag=False,verbose=False):
    numDCMFiles=0
    #temp_dir = tempfile.mkdtemp()
    # niftiPrefix='%s/%s_%s/image' %(temp_dir, scan, scantype)
    # print("dcm2nifti:",dcmDirList, niftiPrefix, project,eid, scanPtr,verbose)
    if project == "sri_incoming" :
        if scanPtr.type == "ncanda-t2fse-v1" and scanPtr.fulldata['data_fields']['parameters/voxelRes/z'] == 2.4 :
            # check if NCANDA0X  that means it comes after NCANDA_ ...
            if  eid > "NCANDA_E11968" or eid.split('_')[0] != "NCANDA" :
                if verbose :
                    print("INFO:only using half the dicom files in " + dcmDirList[0])
                numDCMFiles=int(scanPtr.fulldata['children'][0]['items'][0]['data_fields']['file_count']/2)

    return dcm2nifti(dcmDirList, str(niftiPrefix), numDCMFiles, logFileFlag,verbose)

 
def dcm2nifti(dcmDirList, niftiPrefix, numDCMFiles=0, logFileFlag=False,verbose=False):
    argsTemplate = '--tolerance 1e-3 --write-single-slices --no-progress  --include-ndar --strict-xml  -rvxO %s ' % (niftiPrefix)
    
    if numDCMFiles > 0  :
        if  len(dcmDirList) != 1:
            return str("Creating a nifti from a subset of dicom is currently only implemented for single dicom dir !")
    
        argsCMTK=argsTemplate
        (ecode, sout, eout) = sutils.subset_dcm2image(argsTemplate,dcmDirList[0],numDCMFiles,verbose)

    else :
        #
        # Turn dicoms into niftis 
        #
        argsCMTK=argsTemplate +  ' '.join( dcmDirList ) + " 2>&1"
        (ecode, sout, eout) = sutils.dcm2image(argsCMTK,verbose)
        
    if ecode:  
        return str("The following command failed: %s" % (sutils.dcm2image_cmd +  argsCMTK + " ! msg : " + str(eout)))
        
    # Needed as we check for dcm2image.log when rerunning the case - should come up with better mechanism
    if  logFileFlag :
        logFileName = '%s/dcm2image.log' % (os.path.dirname(niftiPrefix))
        output_file = open(logFileName, 'w')
        try:
            output_file.writelines(sout.decode('utf-8'))
        finally:
            output_file.close()

    return ""

def find_dicom_path(xnat_dir,xnat_scan):
    match = re.match(r'.*('+ xnat_dir + '/.*)scan_.*_catalog.xml.*',XNATSessionElementUtil(xnat_scan).xml,re.DOTALL)
    if not match:
        errMSG="XNAT scan info fails to contain catalog.xml location!" 
        return (errMSG , 0)
 
    dicom_path = match.group(1)
    if not os.path.exists(dicom_path):
        #try another description
        dicom_path = re.sub(r'storage/XNAT', 'ncanda-xnat', dicom_path)
        if not os.path.exists(dicom_path):
            errorMSG = ("Path %s does not exist - export_to_nifti failed!" % (dicom_path))
            return (errorMSG,0)

    return ("",dicom_path)
        
def export_to_nifti(experiment, scanID, xnat_dir, verbose=False):
    subject = experiment.subject_id
    sessionEid = experiment.id
    sessionLabel = experiment.label
    scanPtr=experiment.scans[scanID]
    scanType=scanPtr.type
    if verbose:
        print("Export nifti files for ", subject, sessionEid, sessionLabel, scanID, scanType,xnat_dir)

    error_msg = []
    (errMSG,dicomDir)= find_dicom_path(xnat_dir,scanPtr)
    if errMSG != "":
        error_msg.append(errMSG + " SID:%s EID:%s Label: %s SCAN: %s" % (subject, sessionEid,sessionLabel,scanID))
        return error_msg,0
    
    nifti_log_search = glob.glob(re.sub(r'/DICOM/','_%s/dcm2image.log' % (scanType),re.sub( '/SCANS/', '/RESOURCES/nifti/', dicomDir)))

    # if nifti files were created make sure that they are newer than dicom file otherwise recreate them  
    if  nifti_log_search != [] :
        # we changed code here from *.* to avoid getting errors of not finding dicom files for sessions such as
        # NCANDA_E01386 / B-00454-M-9-20140214 - scan 1 /ncanda-localizer-v1
        dicom_file_pattern = dicomDir + '*'
        dicom_file_list = glob.glob(dicom_file_pattern)
        # ommit xml file - so that only dicom  files are left - xml file is updated every time somebody changes something in the gui for that session - which has no meaning for xml file 
        dicom_file_list =  [x for x in dicom_file_list if '.xml' not in x ]
        # if dicom file is not there something odd is going on
        if dicom_file_list == [] :
            slog.info(sessionLabel, "Error: could not find dicom files ",
                      session=sessionEid,
                      subject=subject,
                      scan_number=scanID,
                      scan_type=scanType,
                      dicom_log_file=dicom_file_pattern)
            return error_msg,0

        # check time stamp - if newer than there is nothing to do
        nifti_time = time.strftime('%Y-%m-%d %H:%m:%S',time.gmtime(os.path.getmtime(nifti_log_search[0])))
        dicom_time = time.strftime('%Y-%m-%d %H:%m:%S',time.gmtime(os.path.getmtime(dicom_file_list[0])))
        if nifti_time > dicom_time  :
            if verbose:
                print("... nothing to do as nifti files are up to date")
            return error_msg,0

        if (nifti_time < str(datetime.datetime.now() - datetime.timedelta(31)).split('.')[0]):
            slog.info(sessionLabel + "_" + scanID, "Error: nifti seems outdated by more than a month (dicom > nifti time)!", 
                  session=sessionEid,
                  subject=subject,
                  check_nifti = str(nifti_time) + " " +  str(nifti_log_search[0]),
                  check_dicom = str(dicom_time) + " " + str(dicom_file_list[0]),
                  xnat_log = "To see which user modified files, refer to the [XNAT Log](https://ncanda.sri.com/xnat/app/action/SearchAction/element/wrk%3AworkflowData/querytype/new)",
                  info =  "If correct, delete nifti in xnat and rerun script for this subject. If incorrect set time stamp of the Dicom file earlier than the  nifti file. Rerun script to make sure that error is resolved !" )
            return error_msg,0
        
        slog.info(sessionLabel + "_" + scanID, "Warning: nifti seem outdated (dicom > nifti time) so they are recreated!", 
                  session=sessionEid,
                  subject=subject,
                  check_nifti = str(nifti_time) + " " +  str(nifti_log_search[0]),
                  check_dicom = str(dicom_time) + " " + str(dicom_file_list[0]),
                  xnat_log = "To see which user modified files, refer to the [XNAT Log](https://ncanda.sri.com/xnat/app/action/SearchAction/element/wrk%3AworkflowData/querytype/new)",
                  info =  "If the issue reappears then simply open up the session in  XNAT, go to 'Manage Files', delete the directory 'Resources/nifti/" + scanType + "'. If the pop-up window does not say that it is deleting 'dicom.log' then most likely you will have to manually delete the directory from the hard drive. To find out, simply run the script again. If the error message still reappears then repeat the previous procedure and afterwards delete the directory that the log file in check_nifti is located!")

    temp_dir = tempfile.mkdtemp()
    niftiPrefix='%s/%s_%s/image%%n.nii' %(temp_dir, scanID, scanType)

    errMsg=dcm2niftiWithCheck([dicomDir], niftiPrefix,experiment.project,sessionEid, scanPtr,True,verbose)
    # dcm2nifti(dicom_Path,niftiPrefix)
    # Clean up - remove temp directory
    if errMsg:
        error_msg.append(errMsg)
        shutil.rmtree(temp_dir)
        return error_msg,0
    
    # Zipping directory with nifti files
    zip_file_name = '%s_%s.zip' % (scanID, scanType)
    zip_path = '%s/%s' % (temp_dir, zip_file_name)
    
    try:
        fzip = zipfile.ZipFile(zip_path, 'w')
        for src in sorted(glob.glob('%s/*/*' % temp_dir)):
            fzip.write(src, re.sub(r'%s/' % temp_dir, '', src))
        fzip.close()
    except Exception as e:
        error_msg.append("Could not zip %s - err_msg: %s" % (zip_path,str(e)))
        # Clean up - remove temp directory
        shutil.rmtree(temp_dir)
        return error_msg,0

    if not os.path.exists(zip_path):
        error_msg.append("Could not zip %s - does not exists !" % (zip_path))
        # Clean up - remove temp directory
        shutil.rmtree(temp_dir)
        return error_msg,0

    try: 
        exp_util=XNATExperimentUtil(experiment) 
        resource=exp_util.resources_insure('nifti')
        resource_util = XNATResourceUtil(resource)
        resource_util.detailed_upload(zip_path, zip_file_name, extract=True, overwrite=True)

    except Exception as e:
        error_msg.append("Unable to upload ZIP file %s to experiment %s" % (zip_path, sessionEid))
        #print("ERROR",str(e))
        #print("DEBUG",error_msg) 
        # sys.exit(0)
        # Clean up - remove temp directory
        shutil.rmtree(temp_dir)
        return error_msg,0


    # Verify image counts for various series
    # images_created = len(glob.glob('%s/*/*.nii.gz' % temp_dir))
    shutil.rmtree(temp_dir)
    return error_msg,1

def init_session(verbose=False) :
    slog.init_log(verbose, False,'make_session_nifti', 'make_session_nifti')
    session = sibispy.Session()
    session.configure()
    session.connect_server('xnat', True)
    return session

#============================================================
# Main
#============================================================
if __name__ == "__main__": 
    import argparse
    parser = argparse.ArgumentParser(description="Turn DICOM into niftis - define '-d and -n'  or '-e, -s, and -n or -u'." )
    parser.add_argument("-d", "--dcmDirList",help="Dicom dir, e.g, /fs/ncanda-xnat/archive/sri_incoming/arc001/B-80447-M-4-20230724/SCANS/3/DICOM. Multiple path can be eperated via ', ' !",action="store")
    parser.add_argument("-e","--eid", help="eid, e.g. NCANDA_E12213",action="store")
    parser.add_argument("-n", "--niftiPrefix",help="nifti prefix, e.g. /tmp/image%n.nii",action="store")
    parser.add_argument("-s","--scan", help="scan number , e.g. 3 . several scans should be seperated with ',' ! can only be used with -n option ",action="store")
    parser.add_argument("-u","--upload", help="After creating nifti, upload to xnat (requireds -e  -s )",action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose operation", action="store_true")
    args = parser.parse_args()

    if args.eid :
        sibis_session=init_session(args.verbose)
        if not sibis_session:
            print("ERROR:Could not connect to xnat!")
            sys.exit(1)

        xnat_dir = sibis_session.get_xnat_dir()
        if not os.path.exists(xnat_dir):
            print("Please ensure {} exists!".format(xnat_dir))
            sys.exit(1)
            
        exp = sibis_session.xnat_get_experiment(args.eid)
        if not exp:
            print("ERROR:Could not find experiment!")
            sys.exit(1)

        if args.upload:
            if len(args.scan.split(',')) != 1 :
                print("ERROR:Exactly define one scan !")
                sys.exit(1)
            
            (errMSG,sucessFlag) = export_to_nifti(exp, args.scan, xnat_dir, args.verbose)

        else:
            subject = exp.subject_id
            project = exp.project
            if args.niftiPrefix == "" :
                print("ERROR: Need to define niftiPrefix")
                sys.exit(1)

            if not args.scan:
                print("ERROR:scan id  needs to be defined !")
                sys.exit(1)
            
            dcmDirList=[]
            for scan in args.scan.split(',') :                
                scan_ptr=exp.scans[scan]
                if not scan_ptr:
                    print("ERROR:Could not find scan!")
                    sys.exit(1)
    
                (errMSG, dcmDir) = find_dicom_path(xnat_dir,scan_ptr)
                if errMSG!= "" :
                    print("ERROR:",errMSG)
                    sys.exit(1)
                    
                dcmDirList.append(dcmDir)

            errMSG=dcm2niftiWithCheck(dcmDirList, args.niftiPrefix, project,args.eid, scan_ptr,True,args.verbose)
    
            # xnat_para = util.mget(scan_attrs)
    elif args.dcmDir != "" :
        errMSG=dcm2niftiWithCheck(args.dcmDir.split(','), args.niftiPrefix, 0, True, args.verbose)

    else:
        errMSG("ERROR: dcmDir or eid and scan have to be defined!")
    
    if errMSG :
        print("ERROR:", errMSG)
        sys.exit(1)
