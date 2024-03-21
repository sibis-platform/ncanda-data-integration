#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

from __future__ import print_function
from builtins import str
import re
import os
import glob
import shutil
import sys
import tempfile 
from sibispy import sibislogger as slog
from sibispy import utils as sutils

from export_mr_sessions_spiral import export_spiral_files

xnatBinDir = os.path.join( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ), 'xnat')
sys.path.append(xnatBinDir)
import make_session_niftis


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

def export_series( redcap_visit_id, xnat, redcap_key, session_and_scan_list, to_directory, filename_pattern, xnat_dir, mr_session_report_complete, verbose=False, timer_label=None):
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

    # We need to create loop here as gradient consists of two scans 
    dicom_path_list = []
    CreateDicomFlag=False
    for session_and_scan in session_and_scan_list.split( ' ' ):
        [ session, scan ] = session_and_scan.split( '/' )
        match = re.match( '.*(' + xnat_dir +'/.*)scan_.*_catalog.xml.*', xnat.raw_text(xnat.select.experiments[ session ].scans[ scan ]), re.DOTALL )
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


    [ session, scan ] = session_and_scan_list.split( ' ' )[0].split('/')
    if len(pipeline_file_list)  :
        if mr_session_report_complete > 1: 
            slog.info(redcap_visit_id  + "_" + scan,"INFO: MRI of pipeline seem outdated",
                      file = to_path_pattern,
                      experiment_xnat_id=session,
                      session_scan_list = session_and_scan_list,
                      info = "File date of " + pipeline_file_list[0] + " was older than " + xnat_file_search[0] + ". If the files should not be updated simply ignore issue.  If it should be update please set the 'complete status' of MRI Session Report to 'Incomplete' and run script again! " 
            )
            return False
            
        slog.info(redcap_visit_id  + "_" + scan,"Warning: existing MR images of the pipeline are updated",
                  file = to_path_pattern,
                  experiment_xnat_id=session,
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

    if len( dicom_path_list ):
        temp_dir = tempfile.mkdtemp()
        # to_path_pattern = os.path.join( to_directory, filename_pattern )
        tmp_path_pattern = os.path.join(temp_dir, filename_pattern )
        if timer_label :
            slog.startTimer2() 

        exp=xnat.select.experiments[ session ]

        eout=make_session_niftis.dcm2niftiWithCheck(dicom_path_list , tmp_path_pattern,exp.project,session, exp.scans[ scan ], False,verbose)
        
        # args= '--tolerance 1e-3 --write-single-slices  --include-ndar --strict-xml --no-progress -rxO %s %s 2>&1' % ( , ' '.join( dicom_path_list ))
        # (ecode, sout, eout) = sutils.dcm2image(args)
        if eout != "":
            slog.info(redcap_visit_id + "_" + scan,"Error: Unable to create dicom file",
                      experiment_site_id=session,
                      cmd=sutils.dcm2image_cmd + " " + args,
                      err_msg = str(eout))
            shutil.rmtree(temp_dir)
            return False

        if timer_label:
            slog.takeTimer2('convert_dicom_to_nifti', timer_label) 

        try:
            if not os.path.exists(to_directory):
                os.makedirs(to_directory)

            open( eid_file_path, 'w' ).writelines( session_and_scan_list )
        except:
            error = "ERROR: unable to write EID file"
            slog.info(redcap_visit_id + "_" + scan,error,
                      experiment_site_id=session,
                      eid_file_path = eid_file_path)

        try: 
            for f in os.listdir(temp_dir):
                shutil.move(os.path.join(temp_dir,f),to_directory)

        except Exception as err_msg: 
            error = "ERROR: unable to move files"
            slog.info(redcap_visit_id + "_" + scan,error,
                      experiment_site_id = session,
                      src_dir = temp_dir ,
                      dest_dir = to_directory,
                      err_msg = str(err_msg))
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
def copy_adni_phantom_t1w( redcap_visit_id, xnat, xnat_eid, to_directory ):
    # Check if target file already exists
    phantom_path = os.path.join( to_directory, 'phantom_t1.nii.gz' )
    if os.path.exists( phantom_path ):
        return False

    # Get XNAT experiment object
    experiment = xnat.select.experiments[ xnat_eid ]

    # Get list of resource files that match the T1w image file name pattern
    experiment_files = []
    resource_list=get_resource_list(redcap_visit_id,xnat,xnat_eid,experiment.resources)
    for resource in resource_list:
        experiment_files += [ (file['cat_ID'], re.sub( '.*\/files\/', '', file['URI']) ) for file in resource if re.match( '^t1.nii.gz$', file['Name'] ) ]

    # No matching files - nothing to do
    if len( experiment_files ) == 0:
        return False

    # Get first file from list, warn if more files
    (phantom_resource, phantom_file) = experiment_files[0]
    experiment.resources[phantom_resource].files[ phantom_file ].download( phantom_path, verbose=False )

    return True

#
# Copy ADNI phantom XML file for structural session
#
# Returns - True if new file as created, False if not
#
def copy_adni_phantom_xml( redcap_visit_id, xnat, xnat_eid, to_directory ):
    # Check if target file already exists
    phantom_path = os.path.join( to_directory, 'phantom.xml' )
    if os.path.exists( phantom_path ):
        return False

    # Get XNAT experiment object
    experiment = xnat.select.experiments[ xnat_eid ]

    # Get list of resource files that match the phantom XML file name pattern
    experiment_files = []
    resource_list=get_resource_list(redcap_visit_id,xnat,xnat_eid,experiment.resources)
    for resource in resource_list:
        experiment_files += [ (file['cat_ID'], re.sub( '.*\/files\/', '', file['URI']) ) for file in resource if re.match( '^phantom.xml$', file['Name'] ) ]

    # No matching files - nothing to do
    if len( experiment_files ) == 0:
        return False

    # Get first file from list, warn if more files
    (phantom_resource, phantom_file) = experiment_files[0]
    experiment.resources[ phantom_resource ].files[ phantom_file ].download( phantom_path, verbose=False )

    return True

#
# Compress physio file in pipeline workdir
#
def gzip_physio( physio_file_path ):
    (ecode,sout,eout) = sutils.gzip('-9f ' + str(physio_file_path))
    if ecode : 
        error = "ERROR: unable to compress physio file"
        slog.info(physio_file_path,error, err_msg = str(eout))

def get_resource_list(redcap_visit_id,xnat,xnat_eid,exp_resources):

    resource_list=[]
    for resource in exp_resources.listing:
        uri='/data/experiments/%s/resources/%s/files' % ( xnat_eid, resource.id )
        try : 
            json_data=xnat._get_json(uri)
            resource_list.append(json_data)

            # ==== test code === 
            for file in json_data:
                if file['cat_ID'] != resource.id :
                    raise RuntimeError("cat_id was different than resource.id for", uri,str(file))
            
        except Exception as err_msg:
            slog.info(redcap_visit_id, "WARNING: Could not retrieve" + uri  + " from xnat.", error_msg=str(err_msg),info="Modt likely file data of session is outdated - to update file data load session in xnat, select 'Manage Files', and press 'Update File Data'!", resource_dir=resource.label,resource_id=resource.id)

    return resource_list

# Copy physio files (cardio and respiratory) for resting-state fMRI session
#
# Returns - True if new file as created, False if not
#
def copy_rsfmri_physio_files( redcap_visit_id, xnat, xnat_eid_and_scan, to_directory ):
    # Extract EID and scan from EID/Scan string
    match = re.match( '^(NCANDA_E[0-9]*)/([0-9]+).*', xnat_eid_and_scan )
    if not match:
        return False
    else:
        xnat_eid = match.group( 1 )
        xnat_scan = match.group( 2 )

    # Get XNAT experiment object
    experiment = xnat.select.experiments[ xnat_eid ]

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
    resource_list=get_resource_list(redcap_visit_id,xnat,xnat_eid,experiment.resources)
    for resource in resource_list:
        for (pattern,outfile_name) in list(physio_filename_patterns.items()):
             physio_files += [ (file['cat_ID'], re.sub( '.*\/files\/', '', file['URI']), outfile_name ) for file in resource if re.match( pattern, file['Name'] ) ]

    # No matching files - nothing to do
    if len( physio_files ) == 0:
        return False

    files_created = False
    for physio in physio_files:
        (physio_resource, physio_file, outfile_name) = physio

        # What will be the output file name? Does it already exist?
        physio_file_path = os.path.join( to_directory, outfile_name )
        if not ( os.path.exists( physio_file_path ) or os.path.exists( physio_file_path+'.gz' ) ):
            # Does output directory exist? Create if not
            if not os.path.exists( to_directory ):
                os.makedirs( to_directory )

            # determine a temporary target location
            (fh, physio_file_path_cache) = tempfile.mkstemp(suffix='physio_cache')
            # fh is integer - if object is needed use tempfile.TemporaryFile()
            # fh.close()

            experiment.resources[ physio_resource ].files[ physio_file ].download(physio_file_path_cache, verbose=False)

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
            
            # remove cached file
            shutil.rmtree(physio_file_path_cache, ignore_errors=True)

    return files_created

#
# Copy manual pipeline override files
#
# Returns - True if new file as created, False if not
#
def copy_manual_pipeline_files( redcap_visit_id, xnat, xnat_eid, to_directory ):
    # Get XNAT experiment object
    experiment = xnat.select.experiments[ xnat_eid ]

    # Get list of resource files that match one of the physio file name patterns
    files = []
    resource_list=get_resource_list(redcap_visit_id,xnat,xnat_eid,experiment.resources)
    for resource in resource_list:
        files += [ (file['cat_ID'], re.sub( '.*\/files\/', '', file['URI']) ) for file in resource if file['collection'] == 'pipeline' ]

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

            experiment.resources[resource].files[file_name].download(file_path, verbose=False)
 
            files_created = True

    return files_created


def delete_workdir(workdir, redcap_visit_id, mr_session_report_complete, missing_mri,verbose=False): 
    if os.path.exists(workdir):
        if mr_session_report_complete >1:
            slog.info(redcap_visit_id,"Error:Deletion of directory " + workdir + " violates MRI Session Report being in status 'Complete'!",
                      workdir = workdir,
                      mri_missing_in_xnat = missing_mri, 
                      info = "If those MRIs are missing in XNAT, then set the status of the MRI Session Report to 'Incomplete' and run script again with -f option.  If they are not missing, check that the names of the scans in XNAT are correct!")
            return False
        
        if verbose :
            print("Deleting " + workdir +" because " + missing_mri)
        try :
            shutil.rmtree(workdir)            
        except Exception as err_msg:  
            slog.info(redcap_visit_id,"Error: Could not delete directory " + workdir, 
                      err_msg = str(err_msg))
            return False

    return True 
        

#
# Export MR images and associated data to pipeline directory tree.
#
# Returns - True if new file as created, False if not
#
def export_to_workdir( redcap_visit_id, xnat, session_data, pipeline_workdir, redcap_key, xnat_dir, mr_session_report_complete,stroop=(None,None,None), verbose=False, timerFlag=False):

    new_files_created = False
    
    # Export structural data
    pipeline_workdir_structural_main = os.path.join( pipeline_workdir, 'structural');
    pipeline_workdir_structural_native = os.path.join( pipeline_workdir_structural_main, 'native' );
    if session_data['mri_series_t1'] != '' and session_data['mri_series_t2'] != '' :
        if timerFlag :
            timerLabel = 't1'
        else :
            timerLabel = None

        new_files_created = export_series( redcap_visit_id, xnat, redcap_key, session_data['mri_series_t1'], pipeline_workdir_structural_native, 't1.nii', xnat_dir, mr_session_report_complete, verbose=verbose, timer_label= timerLabel ) 

        new_files_created = export_series( redcap_visit_id, xnat, redcap_key, session_data['mri_series_t2'], pipeline_workdir_structural_native, 't2.nii', xnat_dir, mr_session_report_complete, verbose=verbose) or new_files_created

        # Copy ADNI phantom XML file
        if 'NCANDA_E' in session_data['mri_adni_phantom_eid']:
            new_files_created = copy_adni_phantom_xml( redcap_visit_id, xnat, session_data['mri_adni_phantom_eid'], pipeline_workdir_structural_native ) or new_files_created
            new_files_created = copy_adni_phantom_t1w( redcap_visit_id, xnat, session_data['mri_adni_phantom_eid'], pipeline_workdir_structural_native ) or new_files_created

    else :
        missing_mri=""
        if session_data['mri_series_t1'] == '' :
            missing_mri = "ncanda-t1spgr-v1 "
        if session_data['mri_series_t2'] == '' :
            missing_mri+= "ncanda-t2fse-v1"
        flag = delete_workdir(pipeline_workdir_structural_main,redcap_visit_id,mr_session_report_complete , missing_mri,verbose)
        if not flag:
            return new_files_created 

    # Export diffusion data
    pipeline_workdir_diffusion_main = os.path.join( pipeline_workdir, 'diffusion' );
    pipeline_workdir_diffusion_native = os.path.join(pipeline_workdir_diffusion_main, 'native' );
    if session_data['mri_series_dti6b500pepolar'] != '' and session_data['mri_series_dti60b1000'] != '':
        new_files_created = export_series( redcap_visit_id, xnat, redcap_key, session_data['mri_series_dti6b500pepolar'], os.path.join( pipeline_workdir_diffusion_native, 'dti6b500pepolar' ), 'dti6-%n.nii', xnat_dir, mr_session_report_complete, verbose=verbose ) or new_files_created

        new_files_created = export_series( redcap_visit_id, xnat, redcap_key, session_data['mri_series_dti60b1000'], os.path.join( pipeline_workdir_diffusion_native, 'dti60b1000' ), 'dti60-%n.nii', xnat_dir, mr_session_report_complete, verbose=verbose ) or new_files_created

        if session_data['mri_series_dti30b400'] != '' :
            new_files_created = export_series( redcap_visit_id, xnat, redcap_key, session_data['mri_series_dti30b400'], os.path.join( pipeline_workdir_diffusion_native, 'dti30b400' ), 'dti30-%n.nii', xnat_dir, mr_session_report_complete, verbose=verbose ) or new_files_created

        if session_data['mri_series_dti_fieldmap'] != '':
            new_files_created = export_series( redcap_visit_id, xnat, redcap_key, session_data['mri_series_dti_fieldmap'], os.path.join( pipeline_workdir_diffusion_native, 'fieldmap' ), 'fieldmap-%T%N.nii', xnat_dir, mr_session_report_complete, verbose=verbose ) or new_files_created
        

    else :
        missing_mri=""
        if session_data['mri_series_dti6b500pepolar'] == '' :
            missing_mri = "ncanda-dti6b500pepolar-v1 "
        if session_data['mri_series_dti60b1000'] == '':
            missing_mri+= "ncanda-dti60b1000-v1"
        flag = delete_workdir(pipeline_workdir_diffusion_main,redcap_visit_id,mr_session_report_complete , missing_mri,verbose)
        if not flag:
            return new_files_created 
        
    # Export EPI functional data (from DICOM files)
    pipeline_workdir_functional_main = os.path.join( pipeline_workdir, 'restingstate');
    pipeline_workdir_functional_native = os.path.join( pipeline_workdir_functional_main, 'native' );
    if session_data['mri_series_rsfmri'] != '' and session_data['mri_series_rsfmri_fieldmap'] != '':
        if timerFlag :
            timerLabel = 'rsfmri' 
        else :
            timerLabel = None

        new_files_created = export_series( redcap_visit_id, xnat, redcap_key, session_data['mri_series_rsfmri'], os.path.join( pipeline_workdir_functional_native, 'rs-fMRI' ), 'bold-%n.nii', xnat_dir, mr_session_report_complete,verbose=verbose, timer_label = timerLabel ) or new_files_created
        # Copy rs-fMRI physio files
        new_files_created = copy_rsfmri_physio_files( redcap_visit_id, xnat, session_data['mri_series_rsfmri'], os.path.join( pipeline_workdir_functional_native, 'physio' ) ) or new_files_created

        new_files_created = export_series( redcap_visit_id, xnat, redcap_key, session_data['mri_series_rsfmri_fieldmap'], os.path.join( pipeline_workdir_functional_native, 'fieldmap' ), 'fieldmap-%T%N.nii', xnat_dir, mr_session_report_complete, verbose=verbose ) or new_files_created

    else :
        missing_mri=""
        if session_data['mri_series_rsfmri'] == '' :
            missing_mri = "ncanda-rsfmri-v1 "
        if  session_data['mri_series_rsfmri_fieldmap'] == '':
            missing_mri+= "ncanda-grefieldmap-v1"
        flag = delete_workdir(pipeline_workdir_functional_main,redcap_visit_id,mr_session_report_complete , missing_mri,verbose)
        if not flag:
            return new_files_created
        

    # Export spiral functional data (from uploaded resources)
    pipeline_workdir_spiralstroop  =  os.path.join( pipeline_workdir, 'spiralstroop' )
    if session_data['mri_eid_spiral_stroop'] != '':
        new_files_created = export_spiral_files( redcap_visit_id, xnat, redcap_key, session_data['mri_eid_spiral_stroop'], pipeline_workdir_spiralstroop, stroop=stroop, verbose=verbose ) or new_files_created
    else :
        missing_mri="mri spiral stroop"
        flag=delete_workdir(pipeline_workdir_spiralstroop,redcap_visit_id,mr_session_report_complete , missing_mri, verbose)
        if not flag:
            return new_files_created
                            
    pipeline_workdir_spiralrest = os.path.join( pipeline_workdir, 'spiralrest')
    if session_data['mri_eid_spiral_rest'] != '':
        new_files_created = export_spiral_files(redcap_visit_id, xnat, redcap_key, session_data['mri_eid_spiral_rest'], pipeline_workdir_spiralrest, verbose=verbose) or new_files_created
    else :
        missing_mri="mri spiral rest"
        flag = delete_workdir(pipeline_workdir_spiralrest,redcap_visit_id,mr_session_report_complete , missing_mri,verbose)
        if not flag:
            return new_files_created

    # Copy any manual pipeline override files from all involved experiments
    #   First, extract "Experiment ID" part from each "EID/SCAN" string, unless empty, then make into set of unique IDs.
    all_sessions = set( [ eid for eid in [ re.sub( '/.*', '', session_data[series] ) for series in list(session_data.keys()) if 'mri_series_' in series ] if 'NCANDA_E' in eid ] )
    for session in all_sessions:
        new_files_created = copy_manual_pipeline_files( redcap_visit_id, xnat, session, pipeline_workdir ) or new_files_created

    return new_files_created

#
# Translate subject code (ID) and REDCap event name to arm and visit name for file system
#

#
# Export MR session and run pipeline if so instructed
#
def export_and_queue(red2cas, redcap_visit_id, xnat, session_data, redcap_key, pipeline_root_dir, xnat_dir,mr_session_report_complete,stroop=(None,None,None), run_pipeline_script=None, verbose=False, timerFlag = False ):
    (subject_label, event_label) = redcap_key
    # Put together pipeline work directory for this subject and visit
    subject_code = session_data['mri_xnat_sid']
    (arm_code,visit_code,pipeline_workdir_rel) = (None, None, None)
    try:
        (arm_code,visit_code,pipeline_workdir_rel) = red2cas.translate_subject_and_event( subject_code, event_label )
    except:
        slog.info(redcap_visit_id, "ERROR: Event " + event_label + " is not supported yet.")
        return None

    if not arm_code:
        return None 

    pipeline_workdir = os.path.join( pipeline_root_dir, pipeline_workdir_rel )
    
    if verbose:
        print(subject_label,'/',subject_code,'/',event_label,'to',pipeline_workdir)

    new_files_created = export_to_workdir(redcap_visit_id,xnat, session_data, pipeline_workdir, redcap_key, xnat_dir, mr_session_report_complete, stroop=stroop, verbose=verbose, timerFlag= timerFlag)

    if (new_files_created and run_pipeline_script):
        if verbose:
            print('Submitting script',run_pipeline_script,'to process',pipeline_workdir)
        just_pipeline_script=os.path.basename(run_pipeline_script)
        qsub_exe = 'cd %s; %s %s' % ( pipeline_root_dir,run_pipeline_script,pipeline_workdir_rel)
        # Changed title so it is informative when displayed in short form through qsub

        job_title = subject_code[7:] + visit_code[0] + visit_code[9:] + '-' + just_pipeline_script
        log_file = '/fs/ncanda-share/log/export_mr_sessions_pipeline/' + job_title + '.txt'
        red2cas.schedule_cluster_job(qsub_exe,'N%s-Nightly' % (job_title),submit_log=log_file, verbose = verbose)
            
    # It is very important to clear the PyXNAT cache, lest we run out of disk space and shut down all databases in the process
    try:
        xnat.client.clearcache()
    except:
        slog.info("export_mr_sessions_pipeline","WARNING: clearing PyXNAT cache threw an exception - are you running multiple copies of this script?")

    return new_files_created
        

#
# Check to make sure no pipeline data exist for "excluded" subjects
#
def check_excluded_subjects( excluded_subjects, pipeline_root_dir ):
    for subject in excluded_subjects:
        subject_dir = os.path.join( pipeline_root_dir, subject )
        if os.path.exists( subject_dir ):
            error = "ERROR: pipeline directory is from an *excluded* subject and should probable be deleted"
            slog.info(subject_dir,error)
