#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

from __future__ import print_function
from builtins import str
import os
import json
import shutil
import fnmatch
import tempfile

from sibispy import sibislogger as slog
from sibispy import utils as sutils

def export_spiral_files(redcap_visit_id, xnat, redcap_key, resource_location, to_directory, stroop=(None, None, None), verbose=None):
    if verbose:
        print("Exporting spiral files " + resource_location + " to " + to_directory)

    result = False # Nothing updated or created yet
    # resource location contains results dict with path building elements
    # NCANDA_E01696/27630/spiral.tar.gz
    spiral_nifti_out = os.path.join(to_directory, 'native', 'bold4D.nii.gz')
    if not os.path.exists(spiral_nifti_out):
        tmpdir = tempfile.mkdtemp()
        result = do_export_spiral_files(redcap_visit_id, xnat, redcap_key, resource_location, to_directory, spiral_nifti_out, tmpdir)
        shutil.rmtree(tmpdir)

    # Do we have information on Stroop files?
    if stroop[0]:
        stroop_file_out = os.path.join(to_directory, 'native', 'stroop.txt')
        # Stroop file does not exist yet, so create it
        if not os.path.exists( stroop_file_out ):
            tmpdir = tempfile.mkdtemp()

            try:
                stroop_file_path = os.path.join(tmpdir, stroop[2])
                stroop_file_dir = os.path.dirname(stroop_file_path)
                if not os.path.isdir(stroop_file_dir):
                    os.makedirs(stroop_file_dir)
                xnat.select.experiments[stroop[0]].resources[stroop[1]].files[stroop[2]].download(stroop_file_path, verbose=False)
            except IOError as e:
                details = "Error: export_spiral_files: for experiment {0}, failed copying resource {1} file {2} to {3}".format(str(stroop[0]), str(stroop[1]), str(stroop[2]), os.path.join( tmpdir, stroop[2]))
                slog.info(str(redcap_key[0]) + "-" +  str(redcap_key[1]), details, error_obj={ 'message': str(e), 'errno': e.errno, 'filename': e.filename, 'strerror': e.strerror })
                return result

            from sanitize_eprime import copy_sanitize
            copy_sanitize(redcap_visit_id,stroop_file_path, stroop_file_out)
            shutil.rmtree(tmpdir)

            result = True

    if verbose:
        if result: 
            print("...done!")
        else:
            print("...nothing exported!")

    return result


def do_export_spiral_files(redcap_visit_id,xnat, redcap_key, resource_location, to_directory, spiral_nifti_out, tmpdir, verbose=None):
    # Do the actual export using a temporary directory that is managed by the caller
    # (simplifies its removal regardless of exit taken)
    # print "do_export_spiral_files" , str(xnat), str(resource_location), str(to_directory), str(spiral_nifti_out), xnat_eid, str(resource_id), str(resource_file_bname)
    [xnat_eid, resource_id, resource_file_bname] = resource_location.split('/')
    info_str="To find the file in XNAT go to 'Manage Files' -> Resources -> *spiral*"
    
    try : 
        tmp_file_path = os.path.join(tmpdir, "pfiles.tar.gz")
        xnat.select.experiments[xnat_eid].resources[resource_id].files[resource_file_bname].download(tmp_file_path, verbose=False)
    except  Exception as err_msg:
        slog.info(xnat_eid + "_" +  resource_id, "Error: failed to download from xnat " + resource_file_bname, err_msg = str(err_msg), info=info_str)
        return False

    errcode, stdout, stderr = sutils.untar(tmp_file_path, tmpdir)
    if errcode != 0:
        error="ERROR: Unable to un-tar resource file. File is likely corrupt."
        slog.info(redcap_visit_id, error,
                     tempfile_path=tmp_file_path,
                     xnat_eid=xnat_eid,
                     spiral_tar_file=resource_location,
                     err_msg = str(stderr),
                     err_cod = str(errcode),
                     info=info_str)
        return False

    spiral_E_files = glob_for_files_recursive(tmpdir, pattern="E*P*.7")
    if len(spiral_E_files) > 1:
        error = "ERROR: more than one E file found"
        slog.info(redcap_visit_id, error,
                  xnat_eid=xnat_eid,
                  spiral_e_files = ', '.join(spiral_E_files),
                  info=info_str)
        return False

    physio_files = glob_for_files_recursive(tmpdir, pattern="P*.physio")
    if len(physio_files) > 1:
        error = 'More than one physio file found in spiral tar file.'
        slog.info(redcap_visit_id,error,
                  xnat_eid=xnat_eid,
                  tmp_file_path=tmp_file_path,
                  physio_files=physio_files,
                  spiral_tar_file=resource_location,
                  info=info_str)
        return False

    if len(spiral_E_files) == 1:
        # Make directory first
        spiral_dir_out = os.path.join(to_directory, 'native')
        if not os.path.exists(spiral_dir_out):
            os.makedirs(spiral_dir_out)
        # Now try to make the NIfTI
        errcode, stdout, stderr = sutils.make_nifti_from_spiral(spiral_E_files[0], spiral_nifti_out)
        if not os.path.exists(spiral_nifti_out):
            error="Unable to make NIfTI from resource file, please try running makenifti manually"
            slog.info(redcap_visit_id, error,
                      xnat_eid=xnat_eid,
                      spiral_file=spiral_E_files[0],
                      ecode = str(errcode),   
                      eout = str(stderr),
                      sout = str(stdout),
                      info=info_str)
            return False
    else:
        error = "ERROR: no spiral data file found"
        slog.info(redcap_visit_id, error,
                  xnat_eid=xnat_eid,
                  spiral_tar_file=resource_location,
                  info=info_str)
        return False

    if len(physio_files) == 1:
        spiral_physio_out = os.path.join(to_directory, 'native', 'physio')
        shutil.copyfile(physio_files[0], spiral_physio_out)
        (ecode, sout, eout) = sutils.gzip('-9 ' + str(spiral_physio_out))
        return not ecode

    return True


def glob_for_files_recursive(root_dir, pattern):
    """Globs for files with the pattern rules used in bash. """
    match_files = []
    for root, dirs, files in os.walk(root_dir, topdown=False):
        match_files += [os.path.join(root, fname) for fname in files if fnmatch.fnmatch(fname, pattern)]
    return match_files


