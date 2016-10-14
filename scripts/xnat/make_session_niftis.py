#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
import os
import re
import glob
import shutil
import zipfile
import tempfile
import subprocess

import sibis
import check_gradient_tables as cgt

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
                error = 'WARNING: Scan found more images than expected.'
                sibis.logging(session_label, error,
                              session=session,
                              scan=scan,
                              scan_type=scantype,
                              images_created=images_created,
                              expected_images=expected_images)


#
# Export experiment files to NIFTI
#
def export_to_nifti(interface, project, subject, session, session_label,
                    manufacturer, scan, scantype, verbose=False):
    if verbose:
        print("Starting export of nifti files...")
    error_msg = []

    logfile_resource = '%s_%s/dcm2image.log' % (scan, scantype)
    xnat_log = interface.select.project(project).subject(subject).experiment(
        session).resource('nifti').file(logfile_resource)
    if not xnat_log.exists():
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

            else:
                temp_dir = tempfile.mkdtemp()
                zip_path = '%s/%s_%s.zip' % (temp_dir, scan, scantype)

                log_filename = '%s/%s_%s/dcm2image.log' % (
                    temp_dir, scan, scantype)
                dcm2image_command = 'cmtk dcm2image --tolerance 1e-3 ' \
                                    '--write-single-slices --no-progress ' \
                                    '-rvxO %s/%s_%s/image%%n.nii %s 2>&1' % (
                                        temp_dir, scan, scantype, dicom_path)

                try:
                    output = subprocess.check_output(dcm2image_command,
                                                     shell=True)
                except:
                    error_msg.append(
                        "The following command failed: %s" % dcm2image_command)

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
                    manufacturer_u = manufacturer.upper()
                    verify_image_count(session, session_label, scan, scantype,
                                       manufacturer_u, images_created)
                    gradient_map = cgt.get_ground_truth_gradients(session_label)

                    if manufacturer_u == 'SIEMENS':
                        gradients = gradient_map.get('Siemens')
                        if 'dti60b1000' in scantype:
                            xml_file_list = glob.glob(
                                os.path.join(temp_dir,
                                             '%s_%s' % (
                                                 scan,
                                                 scantype), 'image*.nii.xml'))
                            errors = list()
                            try:
                                case_gradients = cgt.get_all_gradients(session_label,
                                    xml_file_list, decimals=3)
                                if len(case_gradients) == len(gradients):
                                    for idx, frame in enumerate(case_gradients):
                                        # if there is a frame that doesn't match,
                                        # report it.
                                        if not (gradients[idx] == frame).all():
                                            errors.append(idx)
                                else:
                                    sibis.logging(
                                        session_label,
                                        "ERROR: Incorrect number of frames.",
                                        case_gradients=str(case_gradients),
                                        expected=str(gradients),
                                        session=session)
                            except AttributeError as error:
                                sibis.logging(
                                    session_label,
                                    "Error: parsing XML files failed.",
                                    xml_file_list=str(xml_file_list),
                                    error=str(error),
                                    session=session)
                            if errors:
                                # key = os.path.join(case, args.arm, args.event
                                # , 'diffusion/native/dti60b1000')
                                key = session_label
                                sibis.logging(
                                    key,
                                    "ERROR: Gradient tables do not match for "
                                    "frames.",
                                    frames=str(errors),
                                    session=session)
                            xml_file = open(xml_file_list[0], 'r')
                            try:
                                for line in xml_file:
                                    match = re.match(
                                        '.*<phaseEncodeDirectionSign>(.+)'
                                        '</phaseEncodeDirectionSign>.*',
                                        line)
                                    if match and match.group(
                                            1).upper() != 'NEG':
                                        error_msg.append(
                                            "Scan %s of type %s in session %s "
                                            "has wrong PE sign %s (expected "
                                            "NEG)" % (scan,
                                                      scantype,
                                                      session_label,
                                                      match.group(1).upper()))

                            except:
                                error_msg.append(
                                    "Cannot read XML sidecar file for scan %s "
                                    "of session %s" % (scan, session_label))

                            finally:
                                xml_file.close()

                # Clean up - remove temp directory
                shutil.rmtree(temp_dir)

    return error_msg
