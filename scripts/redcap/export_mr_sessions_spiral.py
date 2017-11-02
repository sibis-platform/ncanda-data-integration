#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import os
import json
import shutil
import fnmatch
import tempfile

from sibispy import sibislogger as slog
from sibispy import utils as sutils

def export_spiral_files(redcap_visit_id, xnat, redcap_key, resource_location, to_directory, stroop=(None, None, None), verbose=None):
    if verbose:
        print("Exporting spiral files...")

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
            stroop_file_tmp = xnat.select.experiment(stroop[0]).resource(stroop[1]).file(stroop[2]).get_copy(os.path.join( tmpdir, stroop[2]))

            from sanitize_eprime import copy_sanitize
            copy_sanitize(redcap_visit_id,stroop_file_tmp, stroop_file_out)
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
    try : 
        tmp_file_path = xnat.select.experiment(xnat_eid).resource(resource_id).file(resource_file_bname).get_copy(os.path.join(tmpdir, "pfiles.tar.gz"))
    except  Exception as err_msg:
        slog.info(xnat_eid + "_" +  resource_id, "Error: failed to download from xnat " + resource_file_bname, err_msg = str(err_msg))
        return False

    errcode, stdout, stderr = sutils.untar(tmp_file_path, tmpdir)
    if errcode != 0:
        error="ERROR: Unable to un-tar resource file. File is likely corrupt."
        slog.info(redcap_visit_id, error,
                     tempfile_path=tmp_file_path,
                     xnat_eid=xnat_eid,
                     spiral_tar_file=resource_location,
                     err_msg = str(stderr),
                     err_cod = str(errcode))
        return False

    spiral_E_files = glob_for_files_recursive(tmpdir, pattern="E*P*.7")
    if len(spiral_E_files) > 1:
        error = "ERROR: more than one E file found"
        slog.info(redcap_visit_id, error,
                      xnat_eid=xnat_eid,
                      spiral_e_files = ', '.join(spiral_E_files))
        return False

    physio_files = glob_for_files_recursive(tmpdir, pattern="P*.physio")
    if len(physio_files) > 1:
        error = 'More than one physio file found in spiral tar file.'
        slog.info(redcap_visit_id,error,
                      xnat_eid=xnat_eid,
                      tmp_file_path=tmp_file_path,
                      physio_files=physio_files,
                      spiral_tar_file=resource_location)
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
                      sout = str(stdout))
            return False
    else:
        error = "ERROR: no spiral data file found"
        slog.info(redcap_visit_id, error,
                  xnat_eid=xnat_eid,
                  spiral_tar_file=resource_location)
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


