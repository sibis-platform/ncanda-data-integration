#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import os
import re
import tempfile
import shutil
from sibispy import sibislogger as slog
from sibispy import utils as sutils

#
# Check for Stroop data (ePrime log file) in given XNAT session
#
import_bindir = os.path.join( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ), 'import', 'laptops' )
bindir = os.path.dirname( os.path.abspath(__file__) )

# Check a list of experiments for ePrime Stroop files
def check_for_stroop( xnat, xnat_eid_list, verbose=False ):
    stroop_files = []
    if verbose : 
        print "check_for_stroop: " + str(xnat_eid_list)

    for xnat_eid in xnat_eid_list:
        experiment = xnat.select.experiment( xnat_eid )

        # Get list of resource files that match the Stroop file name pattern
        for resource in  experiment.resources().get():
            resource_files = xnat._get_json( '/data/experiments/%s/resources/%s/files?format=json' % ( xnat_eid, resource ) );
            stroop_files += [ (xnat_eid, resource, re.sub( '.*\/files\/', '', file['URI']) ) for file in resource_files if re.match( '^NCANDAStroopMtS_3cycles_7m53stask_.*.txt$', file['Name'] ) ]

    # No matching files - nothing to do
    if len( stroop_files ) == 0:
        if verbose : 
            print "check_for_stroop: no stroop"
        return (None, None, None)

    # Get first file from list, warn if more files
    if len( stroop_files ) > 1:
        error = "ERROR: experiment have/has more than one Stroop .txt file. Please make sure there is exactly one per session."
        for xnat_eid in xnat_eid_list:
            slog.info(xnat_eid,error)
	return (None, None, None)
    if verbose : 
        print "check_for_stroop: Stroop File: " + str(stroop_files[0])

    return stroop_files[0]

# Import a Stroop file into REDCap after scoring
def import_stroop_to_redcap( xnat, stroop_eid, stroop_resource, stroop_file, \
                             redcap_key, verbose=False, no_upload=False, post_to_github=False, time_log_dir=None):
    if verbose:
        print "Importing Stroop data from file %s:%s" % ( stroop_eid, stroop_file )

    # Download Stroop file from XNAT into temporary directory
    experiment = xnat.select.experiment( stroop_eid )
    tempdir = tempfile.mkdtemp()

    try:
        stroop_file_copy_path = os.path.join( tempdir, stroop_file )
        stroop_file_path = experiment.resource( stroop_resource ).file( stroop_file ).get_copy( stroop_file_copy_path )
    except IOError as e:
        slog.info(str(redcap_key[0]) + "-" +  str(redcap_key[1]), 
            "Error: import_mr_sessions_stroop: unable to get copy of resource {0} in file {1} to be saved here: {2}".format(stroop_resource, stroop_file, stroop_file_copy_path),
            error={ 'message': e.message, 'errno': e.errno, 'filename': e.filename, 'strerror': e.strerror, 'args': e.args })
    # Convert downloaded Stroop file to CSV scores file
    cmd = str(os.path.join( import_bindir, "stroop2csv" )) +  ' --mr-session --record ' +  redcap_key[0] + ' --event ' + redcap_key[1] + " " + str(stroop_file_path) + ' ' + str(tempdir) 
    (ecode,sout, serr) = sutils.call_shell_program(cmd)
    if ecode: 
        slog.info(str(redcap_key[0]) + "-" +  str(redcap_key[1]), "Error: import_stroop_to_redcap: failed to run stroop2csv!", cmd = str(cmd), stderr = str(serr), stdout = str(sout))

    added_files = sout

    if len( added_files ):
        if not no_upload:
            # Upload CSV file(s) (should only be one anyway)
            for file in added_files.split( '\n' ):
                if re.match( '.*\.csv$', file ):
                    if verbose:
                        print "Uploading ePrime Stroop scores",file
                    cmd = str(os.path.join( bindir, 'csv2redcap' )) 
                    if post_to_github:
                        cmd += " -p"
                    if time_log_dir:
                        cmd += " -t " + str(time_log_dir)

                    cmd += " " + str(file) 
                    (ecode,sout, serr) = sutils.call_shell_program(cmd)
                    if ecode: 
                        slog.info(str(redcap_key[0]) + "-" + str(redcap_key[1]), "Error: import_stroop_to_redcap: failed to run csv2redcap!", cmd = str(cmd), stderr = str(serr), stdout = str(sout))

            # Upload original ePrime file for future reference
            cmd = str(os.path.join( import_bindir, "eprime2redcap" ))
            if post_to_github: 
                cmd += " -p" 

            cmd += ' --project data_entry --record ' + str(redcap_key[0]) + ' --event ' + str(redcap_key[1]) + ' ' + str(stroop_file_path) +  ' mri_stroop_log_file' 
                
            if verbose:
                print "Uploading ePrime Stroop file",stroop_file_path
                # print " ".join(cmd_array)

            (ecode,sout, serr) = sutils.call_shell_program(cmd)
            if ecode: 
                slog.info(str(redcap_key[0]) + "-" +  str(redcap_key[1]), "Error: import_stroop_to_redcap: failed to run eprime2redcap!", cmd = str(cmd), stderr = str(serr), stdout = str(sout))

    else:
        error = "ERROR: could not convert Stroop file %s:%s" % ( redcap_key[0], stroop_file )
        slog.info(str(redcap_key[0]) + '-' +  str(redcap_key[1]), error,
                      stroop_file = stroop_file)

    shutil.rmtree( tempdir )
