#!/usr/bin/env python
import os
import sys
import glob
import json
import re

import numpy as np
import pandas as pd
from lxml import objectify

import sibis


def read_xml_sidecar(filepath):
    """
    Read a CMTK xml sidecar file.

    Returns
    =======
    lxml.objectify
    """
    abs_path = os.path.abspath(filepath)
    with open(abs_path, 'rb') as fi:
        lines = fi.readlines()
        lines.insert(1, '<root>')
        lines.append('</root>')
    string = ''.join(lines)
    strip_ge = string.replace('dicom:GE:', '')
    strip_dicom = strip_ge.replace('dicom:', '')
    result = objectify.fromstring(strip_dicom)
    return result


def get_array(array_string):
    """
    Parse an array from XML string

    Returns
    =======
    np.array
    """
    l = array_string.text.split(' ')
    return np.fromiter(l, np.float)


def get_gradient_table(parsed_sidecar, decimals=None):
    """
    Get the bvector table for a single image

    Returns
    =======
    np.array (rounded to 1 decimal)
    """
    b_vector = get_array(parsed_sidecar.mr.dwi.bVector)
    b_vector_image = get_array(parsed_sidecar.mr.dwi.bVectorImage)
    b_vector_standard = get_array(parsed_sidecar.mr.dwi.bVectorStandard)
    if not decimals:
        decimals = 1
    return np.around([b_vector,
                      b_vector_image,
                      b_vector_standard],
                     decimals=decimals)


def get_cases(cases_root, arm, event, case=None):
    """
    Get a list of cases from root dir, optionally for a single case
    """
    match = 'NCANDA_S*'
    if case:
        match = case

    case_list = list()
    for cpath in glob.glob(os.path.join(cases_root, match)):
      if os.path.isdir(os.path.join(cpath,arm,event)) : 
        case_list.append(cpath)
  
    return case_list

def get_dti_stack(case, arm=None, event=None):
    if arm:
        path = os.path.join(case, arm)
    else:
        path = os.path.join(case, '*')
    if event:
        path = os.path.join(path, event)
    else:
        path = os.path.join(path, '*')

    path = os.path.join(path, 'diffusion/native/dti60b1000/*.xml')
    return glob.glob(path)


def get_all_gradients(session_label, dti_stack, decimals=None):
    """
    Parses a list of dti sidecar files for subject.

    Returns
    =======
    list of np.array
    """
    gradients_per_frame = list()
    gradients_as_array = np.asanyarray([])
    for xml_path in dti_stack:
        xml_sidecar = read_xml_sidecar(xml_path)
        try:
            gradients_per_frame.append(get_gradient_table(xml_sidecar,
                                                     decimals=decimals))
            gradients_as_array = np.asanyarray(gradients_per_frame)
        except Exception as e:
            sibis.logging(session_label,
                          'ERROR: Could not get gradient table from xml sidecar',
                          script='xnat/check_gradient_tables.py',
                          sidecar=str(xml_sidecar),
                          xml_path=xml_path,
                          error=str(e))
    return gradients_as_array


def get_site_scanner(site):
    """
    Returns the "ground truth" case for gradients.
    """
    site_scanner = dict(A='Siemens',
                        B='GE',
                        C='GE',
                        D='Siemens',
                        E='GE')
    return site_scanner.get(site)


def get_ground_truth_gradients(scanner,decimals):
    """
    Return a dictionary for scanner:gratient
    """
    # Choose arbitrary cases for ground truth
    test_path = '/fs/ncanda-share/pipeline/cases'

    scanner_u = scanner.upper()
    if scanner == 'SIEMENS': 
        scanner_subject = 'NCANDA_S00061'

    elif scanner == 'PRISMA': 
        scanner_subject = 'NCANDA_S00061'
    
    elif scanner == 'GE': 
        scanner_subject = 'NCANDA_S00033'

    else : 
      return []     

    subject_path = os.path.join(test_path, scanner_subject)

    # Get ground truth for standard baseline
    test_arm = 'standard'
    test_event = 'baseline'

    # Gets files for each scanner
    dti_stack = get_dti_stack(subject_path, arm=test_arm, event=test_event)

    dti_stack.sort()

    # Parse the xml files to get scanner specific gradients per frame
    return get_all_gradients(scanner_subject + "_" + test_arm + "_" + test_event, dti_stack, decimals)
    # dict(Siemens=siemens_gradients, GE=ge_gradients)

def check_diffusion(session_label,session,xml_file_list,manufacturer,decimals):
    if len(xml_file_list) == 0 : 
        sibis.logging(session_label,
                      "Error: check_diffusion : xml_file_list is empty ",
                      session=session)
        return 

    truth_gradient = np.array(get_ground_truth_gradients(manufacturer,decimals))
    if len(truth_gradient) == 0 :
        sibis.logging(session_label,
                    'ERROR: check_diffusion: scanner is unknown',
                     session=session,
                     scanner=manufacturer)
        return 

    xml_file_list.sort()

    errorsFrame = list()
    errorsExpected = list()
    errorsActual = list()
    try:
        evaluated_gradients = get_all_gradients(session_label,xml_file_list, decimals)

        if len(evaluated_gradients) == len(truth_gradient):
            for idx, frame in enumerate(evaluated_gradients):
                # if there is a frame that doesn't match,
                # report it.
                if not (truth_gradient[idx] == frame).all():
                    errorsFrame.append(idx)
                    errorsActual.append(frame)
                    errorsExpected.append(truth_gradient[idx])
        else:
            sibis.logging(session_label,"ERROR: Incorrect number of frames.",
                          case_gradients=str(evaluated_gradients),
                          expected=str(truth_gradient),
                          session=session)

    except AttributeError as error:
        sibis.logging(session_label, "Error: parsing XML files failed.",
                      xml_file_list=str(xml_file_list),
                      error=str(error),
                      session=session)
        return

    if errorsFrame:
        sibis.logging(session_label,
                      "Errors in dti601000 gradients for new sessions after comparing with ground_truth.",
                      frames=str(errorsFrame),
                      actualGradients=str(errorsActual),
                      expectedGradients=str(errorsExpected),
                      session=session)

    xml_file = open(xml_file_list[0], 'r')
    try:
        for line in xml_file:
            match = re.match('.*<phaseEncodeDirectionSign>(.+)'
                             '</phaseEncodeDirectionSign>.*',
                             line)
            if match and match.group(1).upper() != 'NEG':
                sibis.logging(session_label,
                              "dti601000 has wrong PE sign (expected NEG).",
                              actual_sign=str(match.group(1).upper()),
                              session=session)

    except AttributeError as error:
        sibis.logging(session_label, "Error: parsing XML files failed.",
                      xml_file=xml_file_list[0],
                      error=str(error),
                      session=session)
    finally:
        xml_file.close()

    return

                     
def main(args=None):
    # Get the gradient tables for all cases and compare to ground truth
    if args.verbose:
      print "Checking cases in " + args.base_dir 

    cases = get_cases(args.base_dir, arm=args.arm, event=args.event, case=args.case)

    if cases == [] : 
      print "Error: Did not find any cases matching :" + args.base_dir + "/" + args.case + "/" + args.arm + "/" + args.event
      sys.exit(1)

    # Demographics from pipeline to grab case to scanner mapping
    demo_path = '/fs/ncanda-share/pipeline/summaries/redcap/demographics.csv'
    demographics = pd.read_csv(demo_path, index_col=['subject',
                                                     'arm',
                                                     'visit'])

    # gradient_map = dict(Siemens=get_ground_truth_gradients('Siemens',args.decimals), GE=get_ground_truth_gradients('GE',args.decimals))

    for case in cases:
        # Get the case's site
        if args.verbose:
          print "Processing: " + case 
        sid = os.path.basename(case)
        site = demographics.xs([sid, args.arm, args.event])['site']
        scanner = get_site_scanner(site)
        key = os.path.join(case, args.arm, args.event,'diffusion/native/dti60b1000')
        xml_file_list = get_dti_stack(case, arm=args.arm, event=args.event)
        check_diffusion(key,"",xml_file_list,scanner,args.decimals)

if __name__ == '__main__':
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="check_gradient_tables.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('-a', '--arm', dest="arm",
                        help="Study arm. {}".format(default),
                        default='standard')
    parser.add_argument('-b', '--base-dir', dest="base_dir",
                        help="Study base directory. {}".format(default),
                        default='/fs/ncanda-share/pipeline/cases')
    parser.add_argument('-d', '--decimals', dest="decimals",
                        help="Number of decimals. {}".format(default),
                        default=3)
    parser.add_argument('-e', '--event', dest="event",
                        help="Study event. {}".format(default),
                        default='baseline')
    parser.add_argument('-c', '--case', dest="case",
                        help="Case to check - if none are defined then it checks all cases in that directory. {}".format(default), default=None)
    parser.add_argument('-v', '--verbose', dest="verbose",
                        help="Turn on verbose", action='store_true')
    argv = parser.parse_args()
    sys.exit(main(argv))
