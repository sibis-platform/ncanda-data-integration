#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision$
##  $LastChangedBy$
##  $LastChangedDate$
##

import re
import os
import subprocess
import shutil
import sys

from export_mr_sessions_spiral import export_spiral_files

#
# Checker whether an EID file exists and has the same experiment ID and (if applicable) scan number stored in it.
#
# Returns - True is file exists and has correct (still current) value in it
#
def check_eid_file( eid_file_path, session_and_scan_string ):
    # File content still current?
    try:
        if open( eid_file_path, 'r' ).read().strip() == session_and_scan_string:
            return True
    except:
        # Something went wrong with open and/or read, so say file doesn't exist
        pass

    return False

#
# Export one series to pipeline tree, unless it already exists there
#
# Returns - True if new files were created, False if not
#
def export_series( xnat, session_and_scan_list, to_directory, filename_pattern, verbose=False ):
    # List should have at least one "SESSION/SCAN" entry
    if not '/' in session_and_scan_list:
        return False

    # Put together target directory and filename pattern
    to_path_pattern = os.path.join( to_directory, filename_pattern )

    # If filename is a pattern with substitution, check whether entire directory exists
    if '%' in filename_pattern:
        eid_file_path = os.path.join( to_directory, 'eid' )
        if os.path.exists( to_directory ):
            if check_eid_file( eid_file_path, session_and_scan_list ):
                return False
    else:
        eid_file_path = re.sub( '\.[^/]*', '.eid', to_path_pattern )
        if os.path.exists( to_path_pattern ) or os.path.exists( to_path_pattern + '.gz' ):
            if check_eid_file( eid_file_path, session_and_scan_list ):
                return False

    dicom_path_list = []
    for session_and_scan in session_and_scan_list.split( ' ' ):
        [ session, scan ] = session_and_scan.split( '/' )
        match = re.match( '.*(/fs/storage/XNAT/.*)scan_.*_catalog.xml.*', xnat.select.experiment( session ).scan( scan ).get(), re.DOTALL )
        if match:
            dicom_path = match.group(1)
            if not os.path.exists( dicom_path ):
                dicom_path = re.sub( 'storage/XNAT', 'ncanda-xnat', dicom_path )

            dicom_path_list.append( dicom_path )

    dcm2image_output = None
    if len( dicom_path_list ):
        try:
            dcm2image_command = 'cmtk dcm2image --tolerance 1e-3 --write-single-slices --no-progress -rxO %s %s 2>&1' % ( to_path_pattern, ' '.join( dicom_path_list ) )

            if ( verbose ):
                print dcm2image_command

            dcm2image_output = subprocess.check_output( dcm2image_command, shell=True )
        except:
            if dcm2image_output:
                output_file = open( to_path_pattern + '.log' , 'w' )
                try:
                    output_file.writelines( dcm2image_output )
                except:
                    print dcm2image_output
                finally:
                    output_file.close()
            return False

        try:
            open( eid_file_path, 'w' ).writelines( session_and_scan_list )
        except:
            print "ERROR: unable to write EID file",eid_file_path

        return True
    return False

#
# Copy ADNI phantom T1w image file for structural session
#
# Returns - True if new file as created, False if not
#
def copy_adni_phantom_t1w( xnat, xnat_eid, to_directory ):
    # Check if target file already exists
    phantom_path = os.path.join( to_directory, 'phantom_t1.nii.gz' )
    if os.path.exists( phantom_path ):
        return False

    # Get XNAT experiment object
    experiment = xnat.select.experiment( xnat_eid )

    # Get list of resource files that match the T1w image file name pattern
    experiment_files = []
    for resource in  experiment.resources().get():
        resource_files = xnat._get_json( '/data/experiments/%s/resources/%s/files?format=json' % ( xnat_eid, resource ) );
        experiment_files += [ (resource, re.sub( '.*\/files\/', '', file['URI']) ) for file in resource_files if re.match( '^t1.nii.gz$', file['Name'] ) ]

    # No matching files - nothing to do
    if len( experiment_files ) == 0:
        return False

    # Get first file from list, warn if more files
    (phantom_resource, phantom_file) = experiment_files[0]
    phantom_file_path = experiment.resource( phantom_resource ).file( phantom_file ).get_copy( phantom_path )

    return True

#
# Copy ADNI phantom XML file for structural session
#
# Returns - True if new file as created, False if not
#
def copy_adni_phantom_xml( xnat, xnat_eid, to_directory ):
    # Check if target file already exists
    phantom_path = os.path.join( to_directory, 'phantom.xml' )
    if os.path.exists( phantom_path ):
        return False

    # Get XNAT experiment object
    experiment = xnat.select.experiment( xnat_eid )

    # Get list of resource files that match the phantom XML file name pattern
    experiment_files = []
    for resource in  experiment.resources().get():
        resource_files = xnat._get_json( '/data/experiments/%s/resources/%s/files?format=json' % ( xnat_eid, resource ) )
        experiment_files += [ (resource, re.sub( '.*\/files\/', '', file['URI']) ) for file in resource_files if re.match( '^phantom.xml$', file['Name'] ) ]

    # No matching files - nothing to do
    if len( experiment_files ) == 0:
        return False

    # Get first file from list, warn if more files
    (phantom_resource, phantom_file) = experiment_files[0]
    phantom_file_path = experiment.resource( phantom_resource ).file( phantom_file ).get_copy( phantom_path )

    return True

#
# Compress physio file in pipeline workdir
#
def gzip_physio( physio_file_path ):
    try:
        subprocess.check_call( [ 'gzip', '-9f', physio_file_path ] )
    except:
        print "ERROR: unable to compress physio file", physio_file_path

#
# Copy physio files (cardio and respiratory) for resting-state fMRI session
#
# Returns - True if new file as created, False if not
#
def copy_rsfmri_physio_files( xnat, xnat_eid_and_scan, to_directory ):
    # Extract EID and scan from EID/Scan string
    match = re.match( '^(NCANDA_E[0-9]*)/([0-9]+).*', xnat_eid_and_scan )
    if not match:
        return False
    else:
        xnat_eid = match.group( 1 )
        xnat_scan = match.group( 2 )

    # Get XNAT experiment object
    experiment = xnat.select.experiment( xnat_eid )

    # Until we can look for "physio" tagged files, define list of filename patterns. Note that one type of files needs the scan number in the pattern to pick the right one
    physio_filename_patterns = { '.*\.puls' : 'card_data_50hz',
                                 '.*\.resp' : 'resp_data_50hz',
                                 'cardiac_.*_%s' % xnat_scan : 'card_time_data_100hz',
                                 'respir_.*_%s' % xnat_scan : 'resp_time_data_100hz',
                                 'D.*\.txt' : 'card_trig_data_resp_data_1000hz',
                                 'PPGData.*_epiRT' : 'card_data_100hz',
                                 'PPGTrig.*_epiRT' : 'card_trig_100hz',
                                 'RESPData.*_epiRT' : 'resp_data_25hz',
                                 'RESPTrig.*_epiRT' : 'resp_trig_25hz' }

    # Get list of resource files that match one of the physio file name patterns
    physio_files = []
    for resource in experiment.resources().get():
        resource_files = xnat._get_json( '/data/experiments/%s/resources/%s/files?format=json' % ( xnat_eid, resource ) )
        for (pattern,outfile_name) in physio_filename_patterns.iteritems():
            physio_files += [ (resource, re.sub( '.*\/files\/', '', file['URI']), outfile_name ) for file in resource_files if re.match( pattern, file['Name'] ) ]

    # No matching files - nothing to do
    if len( physio_files ) == 0:
        return False

    files_created = False
    for physio in physio_files:
        (physio_resource, physio_file,outfile_name) = physio

        # What will be the output file name? Does it already exist?
        physio_file_path = os.path.join( to_directory, outfile_name )
        if not ( os.path.exists( physio_file_path ) or os.path.exists( physio_file_path+'.gz' ) ):
            # Does output directory exist? Create if not
            if not os.path.exists( to_directory ):
                os.makedirs( to_directory )

            physio_file_path_cache = experiment.resource( physio_resource ).file( physio_file ).get()

            if not '.txt' in physio_file:
                shutil.move( physio_file_path_cache, physio_file_path )
                gzip_physio( physio_file_path )
                files_created = True
            elif not 'Stroop' in physio_file:
                # Siemens add-on single file
                try:
                    to_file = open( physio_file_path, 'w' )
                    for line in open( physio_file_path_cache ).readlines():
                        match = re.match( '^.* - Voltage - (.*)\t.* - Voltage - (.*)\t.* - Voltage - (.*)$', line )
                        if match:
                            to_file.write( '%s\t%s\t%s\n' % ( match.group(1), match.group(2), match.group(3) ) )
                        else:
                            match = re.match( '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{1,4}\s+(.*)\s+[0-9]{1,2}/[0-9]{1,2}/[0-9]{1,4}\s+(.*)\s+[0-9]{1,2}/[0-9]{1,2}/[0-9]{1,4}\s+(.*)$', line )
                            if match:
                                to_file.write( '%s\t%s\t%s\n' % ( match.group(1), match.group(2), match.group(3) ) )
                            else:
                                to_file.write( line )

                    gzip_physio( physio_file_path )
                    files_created = True
                finally:
                    to_file.close()

    return files_created

#
# Copy manual pipeline override files
#
# Returns - True if new file as created, False if not
#
def copy_manual_pipeline_files( xnat, xnat_eid, to_directory ):
    # Get XNAT experiment object
    experiment = xnat.select.experiment( xnat_eid )

    # Get list of resource files that match one of the physio file name patterns
    files = []
    for resource in experiment.resources().get():
        resource_files = xnat._get_json( '/data/experiments/%s/resources/%s/files?format=json' % ( xnat_eid, resource ) )
        files += [ (resource, re.sub( '.*\/files\/', '', file['URI']) ) for file in resource_files if file['collection'] == 'pipeline' ]

    # No matching files - nothing to do
    if len( files ) == 0:
        return False

    files_created = False
    for (resource,file_name) in files:
        file_path = os.path.join( to_directory, file_name )
        file_dir = os.path.dirname( file_path )
        if not os.path.exists( file_path ):
            # Does output directory exist? Create if not
            if not os.path.exists( file_dir ):
                os.makedirs( file_dir )

            file_path_cache = experiment.resource( resource ).file( file_name ).get()
            shutil.move( file_path_cache, file_path )
            files_created = True

    return files_created

#
# Export MR images and associated data to pipeline directory tree.
#
# Returns - True if new file as created, False if not
#
def export_to_workdir( xnat, session_data, pipeline_workdir, stroop=(None,None,None), verbose=False ):
    new_files_created = False

    # Export structural data
    pipeline_workdir_structural = os.path.join( pipeline_workdir, 'structural', 'native' );
    if session_data['mri_series_t1'] != '':
        new_files_created = export_series( xnat, session_data['mri_series_t1'], pipeline_workdir_structural, 't1.nii', verbose=verbose ) or new_files_created
    if session_data['mri_series_t2'] != '':
        new_files_created = export_series( xnat, session_data['mri_series_t2'], pipeline_workdir_structural, 't2.nii', verbose=verbose ) or new_files_created

    # Copy ADNI phantom XML file
    if 'NCANDA_E' in session_data['mri_adni_phantom_eid']:
        new_files_created = copy_adni_phantom_xml( xnat, session_data['mri_adni_phantom_eid'], pipeline_workdir_structural ) or new_files_created
        new_files_created = copy_adni_phantom_t1w( xnat, session_data['mri_adni_phantom_eid'], pipeline_workdir_structural ) or new_files_created

    # Export diffusion data
    pipeline_workdir_diffusion = os.path.join( pipeline_workdir, 'diffusion', 'native' );
    if session_data['mri_series_dti6b500pepolar'] != '':
        new_files_created = export_series( xnat, session_data['mri_series_dti6b500pepolar'], os.path.join( pipeline_workdir_diffusion, 'dti6b500pepolar' ), 'dti6-%n.nii', verbose=verbose ) or new_files_created
    if session_data['mri_series_dti60b1000'] != '':
        new_files_created = export_series( xnat, session_data['mri_series_dti60b1000'], os.path.join( pipeline_workdir_diffusion, 'dti60b1000' ), 'dti60-%n.nii', verbose=verbose ) or new_files_created
    if session_data['mri_series_dti_fieldmap'] != '':
        new_files_created = export_series( xnat, session_data['mri_series_dti_fieldmap'], os.path.join( pipeline_workdir_diffusion, 'fieldmap' ), 'fieldmap-%T%N.nii', verbose=verbose ) or new_files_created

    # Export EPI functional data (from DICOM files)
    pipeline_workdir_functional = os.path.join( pipeline_workdir, 'restingstate', 'native' );
    if session_data['mri_series_rsfmri'] != '':
        new_files_created = export_series( xnat, session_data['mri_series_rsfmri'], os.path.join( pipeline_workdir_functional, 'rs-fMRI' ), 'bold-%n.nii', verbose=verbose ) or new_files_created
        # Copy rs-fMRI physio files
        new_files_created = copy_rsfmri_physio_files( xnat, session_data['mri_series_rsfmri'], os.path.join( pipeline_workdir_functional, 'physio' ) ) or new_files_created

    if session_data['mri_series_rsfmri_fieldmap'] != '':
        new_files_created = export_series( xnat, session_data['mri_series_rsfmri_fieldmap'], os.path.join( pipeline_workdir_functional, 'fieldmap' ), 'fieldmap-%T%N.nii', verbose=verbose ) or new_files_created

    # Export spiral functional data (from uploaded resources)
    if session_data['mri_eid_spiral_stroop'] != '':
        new_files_created = export_spiral_files( xnat, session_data['mri_eid_spiral_stroop'], os.path.join( pipeline_workdir, 'spiralstroop' ), stroop=stroop, verbose=verbose ) or new_files_created
    if session_data['mri_eid_spiral_rest'] != '':
        new_files_created = export_spiral_files(xnat, session_data['mri_eid_spiral_rest'], os.path.join( pipeline_workdir, 'spiralrest'), verbose=verbose) or new_files_created

    # Copy any manual pipeline override files from all involved experiments
    #   First, extract "Experiment ID" part from each "EID/SCAN" string, unless empty, then make into set of unique IDs.
    all_sessions = set( [ eid for eid in [ re.sub( '/.*', '', session_data[series] ) for series in session_data.keys() if 'mri_series_' in series ] if 'NCANDA_E' in eid ] )
    for session in all_sessions:
        new_files_created = copy_manual_pipeline_files( xnat, session, pipeline_workdir ) or new_files_created

    return new_files_created

#
# Translate subject code (ID) and REDCap event name to arm and visit name for file system
#
event_lookup = {
# Standard arm
    'baseline_visit_arm_1' :    ( 'standard', 'baseline' ),
    '1y_visit_arm_1' :          ( 'standard', 'followup_1y' ),
    '2y_visit_arm_1' :          ( 'standard', 'followup_2y' ),
    '3y_visit_arm_1' :          ( 'standard', 'followup_3y' ),
    '4y_visit_arm_1' :          ( 'standard', 'followup_4y' ),
# Recovery arm
    'recovery_baseline_arm_2' : ( 'recovery', 'baseline' ),
    'recovery_final_arm_2' :    ( 'recovery', 'final' ),
# Maltreated arm
    'baseline_visit_arm_4' :    ( 'maltreated', 'baseline' ),
    '1y_visit_arm_4' :          ( 'maltreated', 'followup_1y' ),
    '2y_visit_arm_4' :          ( 'maltreated', 'followup_2y' ),
    '3y_visit_arm_4' :          ( 'maltreated', 'followup_3y' ),
    '4y_visit_arm_4' :          ( 'maltreated', 'followup_4y' ),}

def translate_subject_and_event( subject_code, event_label ):
    # What Arm and Visit of the study is this event?
    if event_label in event_lookup.keys():
        (arm_code,visit_code) = event_lookup[event_label]
    else:
        raise Exception( "Cannot determine study Arm and Visit from event %s" % event_label )

    pipeline_workdir_rel = os.path.join( subject_code, arm_code, visit_code )
    return (arm_code,visit_code,pipeline_workdir_rel)

#
# Export MR session and run pipeline if so instructed
#
def export_and_queue( xnat, session_data, redcap_key, pipeline_root_dir, stroop=(None,None,None), run_pipeline_script=None, verbose=False ):
    (subject_label, event_label) = redcap_key

    # Put together pipeline work directory for this subject and visit
    subject_code = session_data['mri_xnat_sid']
    (arm_code,visit_code,pipeline_workdir_rel) = (None, None, None)
    try:
        (arm_code,visit_code,pipeline_workdir_rel) = translate_subject_and_event( subject_code, event_label )
    except:
        print "Event",event_label,"is not supported yet."

    if arm_code != None:
        pipeline_workdir = os.path.join( pipeline_root_dir, pipeline_workdir_rel )

        if verbose:
            print subject_label,'/',subject_code,'/',event_label,'to',pipeline_workdir
        new_files_created = export_to_workdir( xnat, session_data, pipeline_workdir, stroop=stroop, verbose=verbose )

        if new_files_created and run_pipeline_script:
            if verbose:
                print 'Submitting script',run_pipeline_script,'to process',pipeline_workdir
            just_pipeline_script=os.path.basename(run_pipeline_script)

            qsub_command = subprocess.Popen( [ '/usr/bin/qsub', '-j', 'oe', '-o', '/dev/null', '-l', 'nodes=1:ppn=4,vmem=32gb', '-N', '%s-%s'%(just_pipeline_script,subject_code) ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
            (stdoutdata, stderrdata) = qsub_command.communicate( 'cd %s; %s %s' % ( pipeline_root_dir,run_pipeline_script,pipeline_workdir_rel) )
            if verbose and (stdoutdata != None):
                print stdoutdata

            #
            # Just temporary for testing - run in parrallel to original pipeline 
            #
            test_pipeline_root_dir='/fs/ncanda-test/pipeline/cases'
            if verbose:
                print 'Testing on ', os.path.join(test_pipeline_root_dir, pipeline_workdir_rel )

            qsub_args= [ '/opt/sge/bin/lx-amd64/qsub','-S','/bin/bash','-cwd','-o','/dev/null','-j','y','-pe','smp','4','-l','h_vmem=32G','-N', 'Nightly-Test-%s' %  (pipeline_workdir_rel) ]
            qsub_exe = 'export SGE_ROOT=/opt/sge; cd %s;  /fs/ncanda-test/pipeline/utils/ncanda_link_data_and_run_pipelines %s' % (test_pipeline_root_dir,pipeline_workdir_rel)
            cmd_str='echo "%s" | %s\n' % (qsub_exe," ".join(qsub_args)) 

            qsub_command = subprocess.Popen( qsub_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
            (stdoutdata, stderrdata) = qsub_command.communicate(qsub_exe)
            if verbose and (stdoutdata != None):
                print stdoutdata
            
            # keep a log to make sure it is working 
            with open("/tmp/ncanda_test_nightly.txt", "a") as myfile:
               myfile.write(cmd)
               myfile.write(stdoutdata) 
            
        # It is very important to clear the PyXNAT cache, lest we run out of disk space and shut down all databases in the process
        try:
            xnat.cache.clear()
        except:
            print "WARNING: clearing PyXNAT cache threw an exception - are you running multiple copies of this script?"

#
# Check to make sure no pipeline data exist for "excluded" subjects
#
def check_excluded_subjects( excluded_subjects, pipeline_root_dir ):
    for subject in excluded_subjects:
        subject_dir = os.path.join( pipeline_root_dir, subject )
        if os.path.exists( subject_dir ):
            print "ERROR: pipeline directory",subject_dir,"is from an *excluded* subject and should probable be deleted"
