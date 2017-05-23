#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
import os
import glob
import shutil
import zipfile
import tempfile
import subprocess
import numpy
import re
from sibispy import sibislogger as slog
import check_gradient_tables as cgt
import time 
import sys 

#
# Verify image count in temp directory created by dcm2image
#

expected_images = dict()
expected_images['GE'] = {'ncanda-t1spgr-v1': [1],
                         'ncanda-mprage-v1': [1],
                         'ncanda-t2fse-v1': [1],
                         'ncanda-dti6b500pepolar-v1': [8],
                         'ncanda-dti60b1000-v1': [62],
                         'ncanda-grefieldmap-v1': [6],
                         'ncanda-rsfmri-v1': [274, 275]}

expected_images['SIEMENS'] = {'ncanda-t1spgr-v1': [1],
                              'ncanda-mprage-v1': [1],
                              'ncanda-t2fse-v1': [1],
                              'ncanda-dti6b500pepolar-v1': [7],
                              'ncanda-dti60b1000-v1': [62],
                              'ncanda-grefieldmap-v1': [1, 2],
                              'ncanda-rsfmri-v1': [274, 275]}


# Make sure we have the right number of volumes for a given series
def verify_image_count(session, session_label, scan, scantype, manufacturer,
                       images_created):
    if manufacturer in expected_images.keys():
        if scantype in expected_images[manufacturer].keys():
            imgrange = expected_images[manufacturer][scantype]
            if not images_created in imgrange:
                error = 'WARNING: Number of frames in archive differ from the standard'
                slog.info(session_label, error,
                              session=session,
                              scan_number=scan,
                              scan_type=scantype,
                              actual_frame_number=images_created,
                              manufacturer=manufacturer,
                              expected_frame_number=str(expected_images[manufacturer][scantype]))


#
# Export experiment files to NIFTI
#
def export_to_nifti(interface, project, subject, session, session_label,
                    manufacturer, scanner_model, scan, scantype, verbose=False, post_to_github=False, time_log_dir=None):
    if verbose:
        print "Starting export of nifti files for ", project, subject, session, session_label, scan, scantype

    error_msg = []

    # logfile_resource = '%s_%s/dcm2image.log' % (scan, scantype)
    # xnat_log = interface.select.project(project).subject(subject).experiment(session).resource('nifti').file(logfile_resource)
    # To test gradient directions without having to delete nifti files in xnat just uncomment this line 
    # and comment out the proceeding one 
    # if not xnat_log.exists() or 'dti60b1000' in scantype:
    # if not xnat_log.exists():
    match = re.match('.*(/fs/storage/XNAT/.*)scan_.*_catalog.xml.*',
                     interface.select.experiment(session).scan(scan).get(),
                     re.DOTALL)
    if match:
            dicom_path = match.group(1)
            if not os.path.exists(dicom_path):
                dicom_path = re.sub('storage/XNAT', 'ncanda-xnat', dicom_path)

            if not os.path.exists(dicom_path):
                error_msg.append(
                    "Path %s does not exist - export_to_nifti failed for SID:"
                    "%s EID:%s Label: %s!" % (dicom_path, subject, session,
                                              session_label))
                return error_msg,0

            # if nifti files were created make sure that they are newer than dicom file otherwise recreate them  
            nifti_log_search = glob.glob(re.sub('/DICOM/','_%s/dcm2image.log' % (scantype),re.sub( '/SCANS/', '/RESOURCES/nifti/', dicom_path)))
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

            temp_dir = tempfile.mkdtemp()
            zip_path = '%s/%s_%s.zip' % (temp_dir, scan, scantype)

            log_filename = '%s/%s_%s/dcm2image.log' % (
                temp_dir, scan, scantype)
            dcm2image_command = 'cmtk dcm2image --tolerance 1e-3 ' \
                                '--write-single-slices --no-progress ' \
                                '-rvxO %s/%s_%s/image%%n.nii %s 2>&1' % (
                                    temp_dir, scan, scantype, dicom_path)

            output = ""
            try:
                output = subprocess.check_output(dcm2image_command,
                                                     shell=True)
            except:
                error_msg.append(
                    "The following command failed %s with the following output %s" % (dcm2image_command,output))

            if len(error_msg) == 0:
                    output_file = open(log_filename, 'w')
                    try:
                        output_file.writelines(output)
                    finally:
                        output_file.close()

                    try:
                        fzip = zipfile.ZipFile(zip_path, 'w')
                        for src in sorted(glob.glob('%s/*/*' % temp_dir)):
                            fzip.write(src, re.sub('%s/' % temp_dir, '', src))
                        fzip.close()
                    except:
                        error_msg.append("Could not zip %s" % zip_path)

            if os.path.exists(zip_path):
                    try:
                        interface.select.project(project).subject(
                            subject).experiment(session).resource(
                            'nifti').put_zip(zip_path, overwrite=True,
                                             extract=True)
                    except:
                        error_msg.append(
                            "Unable to upload ZIP file %s to experiment %s" % (
                                zip_path, session))

            # Verify image counts for various series
            images_created = len(glob.glob('%s/*/*.nii.gz' % temp_dir))

            if images_created > 0:
                    # only use first part of string so GE Manufacturer is turned into GE
                    manufacturer_u = manufacturer.split(' ',1)[0].upper()
                    verify_image_count(session, session_label, scan, scantype,
                                       manufacturer_u, images_created)

                    if 'dti60b1000' in scantype:
                            xml_search_string = os.path.join(temp_dir,'%s_%s' % (scan,scantype), 'image*.nii.xml')
                            xml_file_list = glob.glob(xml_search_string)
                            cgt.check_diffusion(session_label,session,xml_file_list,manufacturer_u,scanner_model, \
                                                decimals=2, post_to_github=post_to_github, time_log_dir=time_log_dir)

            # Clean up - remove temp directory
            shutil.rmtree(temp_dir)

    return error_msg,1
