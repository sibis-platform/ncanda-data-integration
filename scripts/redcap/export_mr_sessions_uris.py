#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

from __future__ import print_function
from builtins import str
import os
import shutil
import fnmatch
import tempfile

from sibispy import sibislogger as slog
from sibispy import utils as sutils


# ---------------------
# Small generic helpers
# ---------------------

def _split_resource_token(token):
    """
    Strictly parse 'EID/RESOURCE_ID/RELATIVE_PATH' (no other formats).
    Returns (eid, rid, rel). 'rel' may include subdirectories.
    """
    try:
        eid, rid, rel = token.strip().split('/', 2)
    except ValueError:
        raise ValueError("Bad resource token (expected 'EID/RID/REL'): {!r}".format(token))
    return eid, rid, rel


def _download_token_to_tempfile(xnat, token, tmpdir, out_basename=None):
    """
    Download the resource file addressed by token to a file in tmpdir.
    Returns absolute local path.
    """
    eid, rid, rel = _split_resource_token(token)
    dst = os.path.join(tmpdir, out_basename or os.path.basename(rel))
    # Use XNAT object API (matches legacy spiral usage)
    xnat.select.experiments[eid].resources[rid].files[rel].download(dst, verbose=False)
    return dst


def glob_for_files_recursive(root_dir, pattern):
    """Globs for files with the pattern rules used in bash."""
    match_files = []
    for root, dirs, files in os.walk(root_dir, topdown=False):
        match_files += [os.path.join(root, fname)
                        for fname in files if fnmatch.fnmatch(fname, pattern)]
    return match_files


# ------------------------------------
# Spiral: unchanged behavior, factored
# ------------------------------------

def _do_export_spiral_files(redcap_visit_id, xnat, redcap_key,
                            resource_token, to_directory,
                            spiral_nifti_out, tmpdir, verbose=None):
    """
    Downloads spiral tar into tmpdir, untars, makes NIfTI + physio.gz.
    Returns True on success, False otherwise.
    """
    info_str = "To find the file in XNAT go to 'Manage Files' -> Resources -> *spiral*"

    # 1) Download the tarball
    try:
        tmp_tar = _download_token_to_tempfile(xnat, resource_token, tmpdir, out_basename="pfiles.tar.gz")
    except Exception as err_msg:
        eid, rid, rel = _split_resource_token(resource_token)
        slog.info("{}_{}".format(eid, rid),
                  "Error: failed to download from xnat {}".format(rel),
                  err_msg=str(err_msg), info=info_str)
        return False

    # 2) Untar
    errcode, stdout, stderr = sutils.untar(tmp_tar, tmpdir)
    if errcode != 0:
        error = "ERROR: Unable to un-tar resource file. File is likely corrupt."
        slog.info(redcap_visit_id, error,
                  tempfile_path=tmp_tar,
                  spiral_tar_file=resource_token,
                  err_msg=str(stderr), err_cod=str(errcode),
                  info=info_str)
        return False

    # 3) Find GE Spiral E-file and optional physio
    spiral_E_files = glob_for_files_recursive(tmpdir, pattern="E*P*.7")
    if len(spiral_E_files) > 1:
        slog.info(redcap_visit_id, "ERROR: more than one E file found",
                  spiral_e_files=', '.join(spiral_E_files), info=info_str)
        return False

    physio_files = glob_for_files_recursive(tmpdir, pattern="P*.physio")
    if len(physio_files) > 1:
        slog.info(redcap_visit_id, 'More than one physio file found in spiral tar file.',
                  tmp_file_path=tmp_tar, physio_files=physio_files,
                  spiral_tar_file=resource_token, info=info_str)
        return False

    if len(spiral_E_files) != 1:
        slog.info(redcap_visit_id, "ERROR: no spiral data file found",
                  spiral_tar_file=resource_token, info=info_str)
        return False

    # 4) Make directory and NIfTI
    spiral_dir_out = os.path.join(to_directory, 'native')
    if not os.path.exists(spiral_dir_out):
        os.makedirs(spiral_dir_out)

    errcode, stdout, stderr = sutils.make_nifti_from_spiral(spiral_E_files[0], spiral_nifti_out)
    if not os.path.exists(spiral_nifti_out):
        slog.info(redcap_visit_id,
                  "Unable to make NIfTI from resource file, please try running makenifti manually",
                  spiral_file=spiral_E_files[0],
                  ecode=str(errcode), eout=str(stderr), sout=str(stdout),
                  info=info_str)
        return False

    # 5) Optional physio.gz
    if len(physio_files) == 1:
        spiral_physio_out = os.path.join(to_directory, 'native', 'physio')
        shutil.copyfile(physio_files[0], spiral_physio_out)
        (ecode, sout, eout) = sutils.gzip('-9 ' + str(spiral_physio_out))
        return not ecode

    return True


# --------------------------------
# Public entry points
# --------------------------------

def export_spiral_files(redcap_visit_id, xnat, redcap_key,
                        resource_location, to_directory,
                        stroop=(None, None, None), verbose=None):
    """
    Backward-compatible wrapper for Spiral:
      - resource_location: 'EID/RID/spiral.tar.gz'
      - Creates:  <to_directory>/native/bold4D.nii.gz
                  <to_directory>/native/physio(.gz) if present
      - If 'stroop' triple given (eid, rid, rel), exports sanitized text to:
                  <to_directory>/native/stroop.txt
    Returns True if anything new was written.
    """
    result = False

    if verbose:
        print("Exporting spiral files {} to {}".format(resource_location, to_directory))

    # Spiral NIfTI
    spiral_nifti_out = os.path.join(to_directory, 'native', 'bold4D.nii.gz')
    if not os.path.exists(spiral_nifti_out):
        tmpdir = tempfile.mkdtemp()
        try:
            ok = _do_export_spiral_files(redcap_visit_id, xnat, redcap_key,
                                         resource_location, to_directory,
                                         spiral_nifti_out, tmpdir, verbose=verbose)
            result = result or ok
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    # Optional Stroop text
    if stroop[0]:
        stroop_file_out = os.path.join(to_directory, 'native', 'stroop.txt')
        if not os.path.exists(stroop_file_out):
            tmpdir = tempfile.mkdtemp()
            try:
                # Download to temp location (preserve subdirs if any)
                tmp_out = os.path.join(tmpdir, stroop[2])
                os.makedirs(os.path.dirname(tmp_out), exist_ok=True)
                xnat.select.experiments[stroop[0]].resources[stroop[1]].files[stroop[2]].download(tmp_out, verbose=False)

                # Sanitize into final location
                from sanitize_eprime import copy_sanitize
                copy_sanitize(redcap_visit_id, tmp_out, stroop_file_out)
                result = True
            except IOError as e:
                details = ("Error: export_spiral_files: for experiment {0}, failed copying resource {1} "
                           "file {2} to {3}").format(str(stroop[0]), str(stroop[1]),
                                                     str(stroop[2]), os.path.join(tmpdir, stroop[2]))
                slog.info(str(redcap_key[0]) + "-" + str(redcap_key[1]),
                          details,
                          error_obj={'message': str(e), 'errno': e.errno,
                                     'filename': e.filename, 'strerror': e.strerror})
                return result
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)

    if verbose:
        print("...done!" if result else "...nothing exported!")

    return result


def export_alcpic_files(redcap_visit_id, xnat, redcap_key,
                        resource_locations, to_directory, verbose=None):
    """
    Download ALCPIC E-Prime files (edat2/txt) referenced by one or more tokens.
      - resource_locations: space-separated string OR list of 'EID/RID/REL'
      - Files are written under: <to_directory>/native/alcpic/<REL>
      - Preserves any subdirectories contained in the REL portion.
    Returns True if at least one new file was saved.
    """
    if verbose:
        print("Exporting alcpic files {} to {}".format(resource_locations, to_directory))

    result = False
    tokens = (resource_locations.split() if isinstance(resource_locations, str)
              else list(resource_locations or []))
    if not tokens:
        if verbose:
            print("...no ALCPIC tokens to export.")
        return result

    base_out = os.path.join(to_directory, 'native', 'eprime')
    os.makedirs(base_out, exist_ok=True)

    for tok in tokens:
        try:
            eid, rid, rel = _split_resource_token(tok)
        except ValueError as ve:
            slog.info(str(redcap_visit_id), "Bad ALCPIC token; skipping", token=str(tok), err=str(ve))
            continue

        # Flatten: always write just the basename into .../native/eprime/
        fname = os.path.basename(rel)
        local_path = os.path.join(base_out, fname)

        if os.path.exists(local_path):
            continue  # idempotent

        tmpdir = tempfile.mkdtemp()
        try:
            tmpfile = _download_token_to_tempfile(xnat, tok, tmpdir, out_basename=fname)
            shutil.move(tmpfile, local_path)
            result = True
        except Exception as err_msg:
            slog.info(f"{eid}_{rid}", "Error: failed to download ALCPIC file",
                      resource_rel=rel, err_msg=str(err_msg))
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    if verbose:
        print("...done!" if result else "...nothing exported!")

    return result
