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

from sibispy import sibislogger as slog
from sibispy import utils as sutils
from sibispy.xnat_util import XNATSessionElementUtil, XNATResourceUtil, XNATExperimentUtil

#
# Export experiment files to NIFTI
#
def export_to_nifti(experiment, subject, session, session_label, scan, scantype, xnat_dir, verbose=False):
    if verbose:
        print("Start export of nifti files for ", subject, session, session_label, scan, scantype,xnat_dir)

    error_msg = []

    # logfile_resource = '%s_%s/dcm2image.log' % (scan, scantype)
    # xnat_log = interface.select.project(project).subject(subject).experiment(session).resource('nifti').file(logfile_resource)
    # To test gradient directions without having to delete nifti files in xnat just uncomment this line 
    # and comment out the proceeding one 
    # if not xnat_log.exists() or 'dti60b1000' in scantype:
    # if not xnat_log.exists():
    match = re.match('.*('+ xnat_dir + '/.*)scan_.*_catalog.xml.*',XNATSessionElementUtil(experiment.scans[scan]).xml,re.DOTALL)
    if not match:
        error_msg.append("XNAT scan info fails to contain catalog.xml location! SID:""%s EID:%s Label: %s SCAN: %s" % (subject, session,session_label,scan))
        return error_msg,0

    dicom_path = match.group(1)
    if not os.path.exists(dicom_path):
        #try another description
        dicom_path = re.sub('storage/XNAT', 'ncanda-xnat', dicom_path)
        if not os.path.exists(dicom_path):
            error_msg.append("Path %s does not exist - export_to_nifti failed for SID:%s EID:%s Label: %s!" % (dicom_path, subject, session,session_label))
            return error_msg,0


    nifti_log_search = glob.glob(re.sub('/DICOM/','_%s/dcm2image.log' % (scantype),re.sub( '/SCANS/', '/RESOURCES/nifti/', dicom_path)))

    # if nifti files were created make sure that they are newer than dicom file otherwise recreate them  
    if  nifti_log_search != [] :
        # we changed code here from *.* to avoid getting errors of not finding dicom files for sessions such as
        # NCANDA_E01386 / B-00454-M-9-20140214 - scan 1 /ncanda-localizer-v1
        dicom_file_pattern = dicom_path + '*'
        dicom_file_list = glob.glob(dicom_file_pattern)
        # ommit xml file - so that only dicom  files are left - xml file is updated every time somebody changes something in the gui for that session - which has no meaning for xml file 
        dicom_file_list =  [x for x in dicom_file_list if '.xml' not in x ]
        # if dicom file is not there something odd is going on
        if dicom_file_list == [] :
            slog.info(session_label, "Error: could not find dicom files ",
                      session=session,
                      subject=subject,
                      scan_number=scan,
                      scan_type=scantype,
                      dicom_log_file=dicom_file_pattern)
            return error_msg,0

        # check time stamp - if newer than there is nothing to do
        nifti_time = time.strftime('%Y-%m-%d %H:%m:%S',time.gmtime(os.path.getmtime(nifti_log_search[0])))
        dicom_time = time.strftime('%Y-%m-%d %H:%m:%S',time.gmtime(os.path.getmtime(dicom_file_list[0])))

        if nifti_time > dicom_time  :
            if verbose:
                print("... nothing to do as nifti files are up to date")
            return error_msg,0


        slog.info(session_label + "_" + scan, "Warning: nifti seem outdated (dicom > nifti time) so they are recreated!", 
                  session=session,
                  subject=subject,
                  check_nifti = str(nifti_time) + " " +  str(nifti_log_search[0]),
                  check_dicom = str(dicom_time) + " " + str(dicom_file_list[0]),
                  info =  "If the issue reappears then simply open up the session in  XNAT, go to 'Manage Files', delete the directory 'Resources/nifti/" + scantype + "'. If the pop-up window does not say that it is deleting 'dicom.log' then most likely you will have to manually delete the directory from the hard drive. To find out, simply run the script again. If the error message still reappears then repeat the previous procedure and afterwards delete the directory that the log file in check_nifti is located!")


    #
    # Turn dicoms into niftis 
    #
    temp_dir = tempfile.mkdtemp()
    args = '--tolerance 1e-3 --write-single-slices --no-progress  --include-ndar --strict-xml  -rvxO %s/%s_%s/image%%n.nii %s 2>&1' % (temp_dir, scan, scantype, dicom_path)
    (ecode, sout, eout) = sutils.dcm2image(args)
    if ecode:  
        error_msg.append("The following command failed: %s" % (sutils.dcm2image_cmd + args + " ! msg : " + str(eout)))
        # Clean up - remove temp directory
        shutil.rmtree(temp_dir)
        return error_msg,0

    # Needed as we check for dcm2image.log when rerunning the case - should come up with better mechanism
    log_filename = '%s/%s_%s/dcm2image.log' % (temp_dir, scan, scantype)
    output_file = open(log_filename, 'w')
    try:
        output_file.writelines(sout.decode('utf-8'))
    finally:
        output_file.close()

    # Zipping directory with nifti files
    zip_file_name = '%s_%s.zip' % (scan, scantype)
    zip_path = '%s/%s' % (temp_dir, zip_file_name)
    
    try:
        fzip = zipfile.ZipFile(zip_path, 'w')
        for src in sorted(glob.glob('%s/*/*' % temp_dir)):
            fzip.write(src, re.sub('%s/' % temp_dir, '', src))
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
        error_msg.append("Unable to upload ZIP file %s to experiment %s" % (zip_path, session))
        print("ERROR",str(e))
        print("DEBUG",error_msg) 
        exit(0)
        # Clean up - remove temp directory
        shutil.rmtree(temp_dir)
        return error_msg,0


    # Verify image counts for various series
    # images_created = len(glob.glob('%s/*/*.nii.gz' % temp_dir))
    shutil.rmtree(temp_dir)
    return error_msg,1
