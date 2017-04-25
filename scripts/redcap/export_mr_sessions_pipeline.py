#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import re
import os
import glob
import subprocess
import shutil
import sys
import tempfile 
from sibisBeta import sibislogger as slog

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
# Checker whether date of file is newer than in xnat 
#
# Returns - True is file is newer 
#
def check_file_date(pipeline_file,xnat_file):
    # File content still current?
    try:
        if os.path.getmtime(pipeline_file) > os.path.getmtime(xnat_file):
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

def export_series( xnat, redcap_key, session_and_scan_list, to_directory, filename_pattern, verbose=False ):
    (subject_label, event_label) = redcap_key
    # List should have at least one "SESSION/SCAN" entry
    if not '/' in session_and_scan_list:
        return False

    # Put together target directory and filename pattern
    to_path_pattern = os.path.join( to_directory, filename_pattern )

    # If filename is a pattern with substitution, check whether entire directory exists
    if '%' in filename_pattern:
        pipeline_file_pattern = re.sub('%T%N','*',re.sub( '%n', '*', to_path_pattern)) + ".xml"
        eid_file_path = os.path.join( to_directory, 'eid' )
    else:
        pipeline_file_pattern = to_path_pattern + ".xml"
        eid_file_path = re.sub( '\.[^/]*', '.eid', to_path_pattern )

    # Check if EID is still the same 
    eid_unchanged_flag = check_eid_file( eid_file_path, session_and_scan_list )
    
    # Check if files are already created 
    pipeline_file_list= glob.glob(pipeline_file_pattern)

    dicom_path_list = []
    CreateDicomFlag=False
    for session_and_scan in session_and_scan_list.split( ' ' ):
        [ session, scan ] = session_and_scan.split( '/' )
        match = re.match( '.*(/fs/storage/XNAT/.*)scan_.*_catalog.xml.*', xnat.select.experiment( session ).scan( scan ).get(), re.DOTALL )
        if match:
            dicom_path = match.group(1)
            if not os.path.exists( dicom_path ):
                dicom_path = re.sub( 'storage/XNAT', 'ncanda-xnat', dicom_path )
            dicom_path_list.append( dicom_path )

            # If pipeline already has created file check date to xnat file - assumes that check_new_sessions is always run before this script otherwise pipeline is run twice ! If not created then or eid changed then create dicoms 
            if eid_unchanged_flag and len(pipeline_file_list) : 
                # Look for xnat file 
                xnat_file_pattern = re.sub('/DICOM/','_*/image*.nii.xml',re.sub( '/SCANS/', '/RESOURCES/nifti/', dicom_path))
                xnat_file_search  = glob.glob(xnat_file_pattern)

                # If date of xnat file is newer than in pipeline then update  
                if  xnat_file_search != [] and not check_file_date(pipeline_file_list[0],xnat_file_search[0]):
                    CreateDicomFlag=True
            else:
                CreateDicomFlag=True

    if CreateDicomFlag == False :
        return False

    if len(pipeline_file_list)  :
        [ session, scan ] = session_and_scan_list.split( ' ' )[0].split('/')
        slog.info(subject_label + "_" + event_label,"Warning: existing MR images of the pipeline are updated",
                      file = to_path_pattern,
                      experiment_xnat_id=session + "_" + scan,
                      session_scan_list = session_and_scan_list )

        # Remove existing files of that type to make sure we start with clean slate
        for xml_file in pipeline_file_list:
            os.remove(xml_file)
            nii_file = re.sub('.nii.xml','.nii',xml_file)
            if os.path.exists(nii_file):
                os.remove(nii_file)
            nii_file += ".gz"
            if os.path.exists(nii_file):
                os.remove(nii_file)

    dcm2image_output = None
    if len( dicom_path_list ):
        temp_dir = tempfile.mkdtemp()
        # to_path_pattern = os.path.join( to_directory, filename_pattern )
        tmp_path_pattern = os.path.join(temp_dir, filename_pattern )
        dcm2image_output = ""
        try:
            dcm2image_command = 'cmtk dcm2image --tolerance 1e-3 --write-single-slices --no-progress -rxO %s %s 2>&1' % ( tmp_path_pattern, ' '.join( dicom_path_list ) )

            if ( verbose ):
                print dcm2image_command

            dcm2image_output = subprocess.check_output( dcm2image_command, shell=True )

        except:
            slog.info(session + "_" + scan,"Error: Unable to create dicom file",
                          cmd=dcm2image_command,
                          output=dcm2image_output)
            shutil.rmtree(temp_dir)
            return False

        try:
            if not os.path.exists(to_directory):
                os.makedirs(to_directory)

            open( eid_file_path, 'w' ).writelines( session_and_scan_list )
        except:
            error = "ERROR: unable to write EID file"
            slog.info(session + "_" + scan,error, eid_file_path = eid_file_path)

        try: 
            for f in os.listdir(temp_dir):
                shutil.move(os.path.join(temp_dir,f),to_directory)

        except Exception as err_msg: 
            error = "ERROR: unable to move files"
            slog.info(session + "_" + scan,error, src_dir = temp_dir , dest_dir = to_directory, err_msg = str(err_msg))
            shutil.rmtree(temp_dir)
            return False

        shutil.rmtree(temp_dir)
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
        error = "ERROR: unable to compress physio file"
        slog.info(physio_file_path,error)

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


def delete_workdir(workdir,redcap_key,verbose=False): 
    if os.path.exists(workdir):
        if verbose :
            print "Deleting " + workdir

        try :
            shutil.rmtree(workdir)            
        except Exception as err_msg:  
            (subject_label, event_label) = redcap_key
            slog.info(subject_label + "_" + event_label,"Error: Could not delete directory", 
                      directory = workdir,
                      err_msg = str(err_msg))

#
# Export MR images and associated data to pipeline directory tree.
#
# Returns - True if new file as created, False if not
#
def export_to_workdir( xnat, session_data, pipeline_workdir, redcap_key, stroop=(None,None,None), verbose=False ):
    new_files_created = False

    # Export structural data
    pipeline_workdir_structural_main = os.path.join( pipeline_workdir, 'structural');
    pipeline_workdir_structural_native = os.path.join( pipeline_workdir_structural_main, 'native' );
    if session_data['mri_series_t1'] != '' and session_data['mri_series_t2'] != '' :
        new_files_created = export_series( xnat, redcap_key, session_data['mri_series_t1'], pipeline_workdir_structural_native, 't1.nii', verbose=verbose ) or new_files_created

        new_files_created = export_series( xnat, redcap_key, session_data['mri_series_t2'], pipeline_workdir_structural_native, 't2.nii', verbose=verbose ) or new_files_created

        # Copy ADNI phantom XML file
        if 'NCANDA_E' in session_data['mri_adni_phantom_eid']:
            new_files_created = copy_adni_phantom_xml( xnat, session_data['mri_adni_phantom_eid'], pipeline_workdir_structural_native ) or new_files_created
            new_files_created = copy_adni_phantom_t1w( xnat, session_data['mri_adni_phantom_eid'], pipeline_workdir_structural_native ) or new_files_created

    else :
        delete_workdir(pipeline_workdir_structural_main,redcap_key,verbose)

    # Export diffusion data
    pipeline_workdir_diffusion_main = os.path.join( pipeline_workdir, 'diffusion' );
    pipeline_workdir_diffusion_native = os.path.join(pipeline_workdir_diffusion_main, 'native' );
    if session_data['mri_series_dti6b500pepolar'] != '' and session_data['mri_series_dti60b1000'] != '' :
        new_files_created = export_series( xnat, redcap_key, session_data['mri_series_dti6b500pepolar'], os.path.join( pipeline_workdir_diffusion_native, 'dti6b500pepolar' ), 'dti6-%n.nii', verbose=verbose ) or new_files_created

        new_files_created = export_series( xnat, redcap_key, session_data['mri_series_dti60b1000'], os.path.join( pipeline_workdir_diffusion_native, 'dti60b1000' ), 'dti60-%n.nii', verbose=verbose ) or new_files_created

        if session_data['mri_series_dti_fieldmap'] != '':
            new_files_created = export_series( xnat, redcap_key, session_data['mri_series_dti_fieldmap'], os.path.join( pipeline_workdir_diffusion_native, 'fieldmap' ), 'fieldmap-%T%N.nii', verbose=verbose ) or new_files_created
    else :
        delete_workdir(pipeline_workdir_diffusion_main,redcap_key,verbose)

    # Export EPI functional data (from DICOM files)
    pipeline_workdir_functional_main = os.path.join( pipeline_workdir, 'restingstate');
    pipeline_workdir_functional_native = os.path.join( pipeline_workdir_functional_main, 'native' );
    if session_data['mri_series_rsfmri'] != '' and session_data['mri_series_rsfmri_fieldmap'] != '':
        new_files_created = export_series( xnat, redcap_key, session_data['mri_series_rsfmri'], os.path.join( pipeline_workdir_functional_native, 'rs-fMRI' ), 'bold-%n.nii', verbose=verbose ) or new_files_created
        # Copy rs-fMRI physio files
        new_files_created = copy_rsfmri_physio_files( xnat, session_data['mri_series_rsfmri'], os.path.join( pipeline_workdir_functional_native, 'physio' ) ) or new_files_created

        new_files_created = export_series( xnat, redcap_key, session_data['mri_series_rsfmri_fieldmap'], os.path.join( pipeline_workdir_functional_native, 'fieldmap' ), 'fieldmap-%T%N.nii', verbose=verbose ) or new_files_created

    else :
        delete_workdir(pipeline_workdir_functional_main,redcap_key,verbose)

    # Export spiral functional data (from uploaded resources)
    pipeline_workdir_spiralstroop  =  os.path.join( pipeline_workdir, 'spiralstroop' )
    if session_data['mri_eid_spiral_stroop'] != '':
        new_files_created = export_spiral_files( xnat, redcap_key, session_data['mri_eid_spiral_stroop'], pipeline_workdir_spiralstroop, stroop=stroop, verbose=verbose ) or new_files_created
    else :
        delete_workdir(pipeline_workdir_spiralstroop,redcap_key,verbose)

    pipeline_workdir_spiralrest = os.path.join( pipeline_workdir, 'spiralrest')
    if session_data['mri_eid_spiral_rest'] != '':
        new_files_created = export_spiral_files(xnat, redcap_key, session_data['mri_eid_spiral_rest'], pipeline_workdir_spiralrest, verbose=verbose) or new_files_created
    else :
        delete_workdir(pipeline_workdir_spiralrest,redcap_key,verbose)


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

        new_files_created = export_to_workdir( xnat, session_data, pipeline_workdir, redcap_key, stroop=stroop, verbose=verbose )

        if new_files_created and run_pipeline_script:
            if verbose:
                print 'Submitting script',run_pipeline_script,'to process',pipeline_workdir
            just_pipeline_script=os.path.basename(run_pipeline_script)

            # Old Cluster 
            # qsub_command = subprocess.Popen( [ '/usr/bin/qsub', '-j', 'oe', '-o', '/dev/null', '-l', 'nodes=1:ppn=4,vmem=32gb', '-N', '%s-%s-%s'%(just_pipeline_script,visit_code, subject_code) ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
            # (stdoutdata, stderrdata) = qsub_command.communicate( 'cd %s; %s %s' % ( pipeline_root_dir,run_pipeline_script,pipeline_workdir_rel) )
            #if verbose and (stdoutdata != None):
            #    print stdoutdata

            #
            # Just temporary for testing - run in parrallel to original pipeline 
            #
            # test_pipeline_root_dir='/fs/ncanda-test/pipeline/cases'
            #if verbose:
            #    print 'Testing on ', os.path.join(test_pipeline_root_dir, pipeline_workdir_rel )
            # qsub_exe = 'cd %s; /fs/ncanda-test/pipeline/scripts/utils/ncanda_link_data_and_run_pipelines %s' % (test_pipeline_root_dir,pipeline_workdir_rel)

            sge_env = os.environ.copy()
            sge_env['SGE_ROOT'] = '/opt/sge' 
            qsub_args= [ '/opt/sge/bin/lx-amd64/qsub','-S','/bin/bash','-o','/dev/null','-j','y','-pe','smp','4','-l','h_vmem=32G','-N', '%s-%s-%s-Nightly' % (subject_code,visit_code,just_pipeline_script) ]
            qsub_exe = 'cd %s; %s %s' % ( pipeline_root_dir,run_pipeline_script,pipeline_workdir_rel)
            cmd_str='echo "%s" | %s\n' % (qsub_exe," ".join(qsub_args)) 
            qsub_command = subprocess.Popen( qsub_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=sge_env)
            (stdoutdata, stderrdata) = qsub_command.communicate(qsub_exe)

            if verbose and (stdoutdata != None):
                print stdoutdata
            
            # keep a log to make sure it is working 
            if verbose:
               print cmd_str

            with open("/tmp/ncanda_test_nightly.txt", "a") as myfile:
               myfile.write(cmd_str)
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
            error = "ERROR: pipeline directory is from an *excluded* subject and should probable be deleted"
            slog.info(subject_dir,error)
