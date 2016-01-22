#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision$
##  $LastChangedBy$
##  $LastChangedDate$
##

import pyxnat
import os.path
import re
import subprocess
import tempfile
import shutil
import glob
import zipfile
import sys

#
# Verify image count in temp directory created by dcm2image
# 

expected_images = dict()
expected_images['GE'] = { 'ncanda-t1spgr-v1' : [1],
                          'ncanda-mprage-v1' : [1],
                          'ncanda-t2fse-v1' :  [1],
                          'ncanda-dti6b500pepolar-v1' : [8],
                          'ncanda-dti60b1000-v1' : [62],
                          'ncanda-grefieldmap-v1' : [6],
                          'ncanda-rsfmri-v1' : [274,275] }

expected_images['SIEMENS'] = { 'ncanda-t1spgr-v1' : [1],
                               'ncanda-mprage-v1' : [1],
                               'ncanda-t2fse-v1' :  [1],
                               'ncanda-dti6b500pepolar-v1' : [7],
                               'ncanda-dti60b1000-v1' : [62],
                               'ncanda-grefieldmap-v1' : [1,2],
                               'ncanda-rsfmri-v1' : [274,275] }

#
# Make sure we have the right number of volumes for a given series
def verify_image_count( session, session_label, scan, scantype, manufacturer, images_created ):
    if manufacturer in expected_images.keys():
        if scantype in expected_images[manufacturer].keys():
            imgrange = expected_images[manufacturer][scantype]
            if not images_created in imgrange:
                error = dict(session_label =  session_label,
                    session = session,
                    scan = scan,
                    scan_type = scantype,
                    images_created = images_created,
                    expected_images = expected_images,
                    error_message = 'WARNING: Scan found more images than expected.'
                )
                print json.dumps(error, sort_keys=True)

                #Old Error Message
                #print 'WARNING: experiment %s(%s), scan %s(%s), found %d images' % ( session_label,session,scan,scantype,images_created), '(expected',imgrange,')'

#
# Export experiment files to NIFTI
#
def export_to_nifti( interface, project, subject, session, session_label, manufacturer, scan, scantype, dry_run=False, verbose=False ):

    images_created = 0
    errorMSG = []

    logfile_resource = '%s_%s/dcm2image.log' % (scan,scantype)
    xnat_log = interface.select.project( project ).subject( subject ).experiment( session ).resource('nifti').file( logfile_resource )
    if not xnat_log.exists():
        match = re.match( '.*(/fs/storage/XNAT/.*)scan_.*_catalog.xml.*', interface.select.experiment( session ).scan( scan ).get(), re.DOTALL )
        if match:
            dicom_path = match.group(1)
            if not os.path.exists( dicom_path ):
                dicom_path = re.sub( 'storage/XNAT', 'ncanda-xnat', dicom_path )

            if not os.path.exists( dicom_path ):
                errorMSG.append("Path %s does not exist - export_to_nifti failed for SID:%s EID:%s Label: %s!" % (dicom_path,  subject, session, session_label))

            else :
                temp_dir = tempfile.mkdtemp()
                zip_path = '%s/%s_%s.zip' % (temp_dir, scan, scantype)
                
                logFileName='%s/%s_%s/dcm2image.log' % (temp_dir,scan,scantype)
                dcm2image_command = 'cmtk dcm2image --tolerance 1e-3 --write-single-slices --no-progress -rvxO %s/%s_%s/image%%n.nii %s 2>&1' % ( temp_dir, scan, scantype, dicom_path )
                
                try:
                    output = subprocess.check_output( dcm2image_command, shell=True )
                except:
                    errorMSG.append("The following command failed: %s" % dcm2image_command) 
                
                if len(errorMSG)==0:
                    output_file = open( logFileName , 'w' )
                    try: 
                        output_file.writelines( output )
                    finally: 
                        output_file.close()            
                
                    try: 
                        fzip = zipfile.ZipFile( zip_path, 'w' )
                        for src in sorted( glob.glob( '%s/*/*' % temp_dir ) ):
                           fzip.write( src, re.sub( '%s/' % temp_dir, '', src ) )
                        fzip.close()
                    except:
                        errorMSG.append("Could not zip %s" % zip_path )
                
                
                if os.path.exists( zip_path ):
                    try:
                        interface.select.project( project ).subject( subject ).experiment( session ).resource('nifti').put_zip( zip_path, overwrite=True, extract=True )
                    except:
                        errorMSG.append("Unable to upload ZIP file %s to experiment %s" % (zip_path,session))
                
                # Verify image counts for various series
                images_created = len( glob.glob( '%s/*/*.nii.gz' % temp_dir ) )
                
                if images_created > 0:
                    manufacturer_u = manufacturer.upper()
                    verify_image_count( session, session_label, scan, scantype, manufacturer_u, images_created )
                    
                    if manufacturer_u == 'SIEMENS':
                        if 'dti6b500pepolar' in scantype:
                            xml_file = open( os.path.join( temp_dir, '%s_%s' % (scan,scantype), 'image1.nii.xml' ), 'r' )
                            try:
                                for line in xml_file:
                                    match = re.match( '.*<phaseEncodeDirectionSign>(.+)</phaseEncodeDirectionSign>.*', line )
                                    if match and match.group(1).upper() != 'POS':
                                        errorMSG.append("Scan %s of type %s in session %s has wrong PE sign %s (expected POS)" % (scan, scantype, session_label, match.group(1).upper()))
                
                            except:
                                errorMSG.append("Cannot read XML sidecar file for scan %s of session %s" % (scan, session_label)) 
                
                            finally:
                                xml_file.close()
                        elif 'dti60b1000' in scantype:
                            xml_file = open( os.path.join( temp_dir, '%s_%s' % (scan,scantype), 'image01.nii.xml' ), 'r' )
                            try:
                                for line in xml_file:
                                    match = re.match( '.*<phaseEncodeDirectionSign>(.+)</phaseEncodeDirectionSign>.*', line )
                                    if match and match.group(1).upper() != 'NEG':
                                        errorMSG.append("Scan %s of type %s in session %s has wrong PE sign %s (expected NEG)" % (scan, scantype, session_label, match.group(1).upper()))
                
                            except:
                                errorMSG.append("Cannot read XML sidecar file for scan %s of session %s" % (scan, session_label)) 
                
                            finally:
                                xml_file.close()
                
                # Clean up - remove temp directory
                shutil.rmtree( temp_dir )

    for MSG in errorMSG : 
        print "ERROR: ", MSG

    return errorMSG 
