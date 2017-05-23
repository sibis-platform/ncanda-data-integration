#!/usr/bin/env python
import os
import sys
import glob
import json
import re
import math 

import numpy as np
import pandas as pd
from lxml import objectify

from sibispy import sibislogger as slog

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

    error_xml_path_list=[] 
    error_msg=""

    for xml_path in dti_stack:
        xml_sidecar = read_xml_sidecar(xml_path)
        try:
            gradients_per_frame.append(get_gradient_table(xml_sidecar,
                                                     decimals=decimals))
            gradients_as_array = np.asanyarray(gradients_per_frame)
        except Exception as e:
            error_xml_path_list.append(xml_path)
            error_msg=str(e)

    if error_xml_path_list != [] :
        slog.info(session_label,
                      'ERROR: Could not get gradient table from xml sidecar',
                      script='xnat/check_gradient_tables.py',
                      sidecar=str(xml_sidecar),
                      error_xml_path_list=str(error_xml_path_list),
                      error_msg=error_msg)
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


def get_ground_truth_gradients(scanner,scanner_model,decimals):
    """
    Return a dictionary for scanner:gratient
    """
    # Choose arbitrary cases for ground truth
    test_path = '/fs/ncanda-share/pipeline/cases'
    # Get ground truth for standard baseline
    test_arm = 'standard'
    test_event = 'baseline'

    scanner_u = scanner.upper()
    if scanner_u == 'SIEMENS': 
        if scanner_model.split('_',1)[0].upper() == "PRISMA" :
            scanner_subject = 'NCANDA_S00689'
            test_event = 'followup_2y'
        else :
            scanner_subject = 'NCANDA_S00061'

    elif scanner_u == 'GE': 
        scanner_subject = 'NCANDA_S00033'

    else : 
      return []     

    subject_path = os.path.join(test_path, scanner_subject)

    # Gets files for each scanner
    dti_stack = get_dti_stack(subject_path, arm=test_arm, event=test_event)

    dti_stack.sort()

    # Parse the xml files to get scanner specific gradients per frame
    return get_all_gradients(scanner_subject + "_" + test_arm + "_" + test_event, dti_stack, decimals)
    # dict(Siemens=siemens_gradients, GE=ge_gradients)

def check_diffusion(session_label,session,xml_file_list,manufacturer,scanner_model,decimals, post_to_github, time_log_dir):
    if len(xml_file_list) == 0 : 
        slog.info(session_label,
                      "Error: check_diffusion : xml_file_list is empty ",
                      session=session)
        return 

    truth_gradient = np.array(get_ground_truth_gradients(manufacturer,scanner_model,decimals))
    if len(truth_gradient) == 0 :
        slog.info(session_label,
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
            slog.info(session_label,"ERROR: Incorrect number of frames.",
                          number_of_frames=str(len(evaluated_gradients)),
                          expected=str(len(truth_gradient)),
                          session=session)

    except AttributeError as error:
        slog.info(session_label, "Error: parsing XML files failed.",
                      xml_file_list=str(xml_file_list),
                      error_msg=str(error),
                      session=session)
        return

    if errorsFrame:
        slog.info(session_label,
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
                slog.info(session_label,
                              "dti601000 has wrong PE sign (expected NEG).",
                              actual_sign=str(match.group(1).upper()),
                              session=session)

    except AttributeError as error:
        slog.info(session_label, "Error: parsing XML files failed.",
                      xml_file=xml_file_list[0],
                      error=str(error),
                      session=session)
    finally:
        xml_file.close()

    return

                     
def main(args=None):
    # Get the gradient tables for all cases and compare to ground truth
    post_to_github = False
    time_log_dir = None
    global records
    global uploads
    uploads = 0

    if args.verbose:
        print "Checking cases in " + args.base_dir

    if args.post_to_github:
        post_to_github = args.post_to_github

    if args.time_log_dir:
        time_log_dir = args.time_log_dir

    cases = get_cases(args.base_dir, arm=args.arm, event=args.event, case=args.case)
    records = len(cases)

    if cases == [] : 
        if args.case :
            case=  args.case
        else :
            case = "*"

        print "Error: Did not find any cases matching :" + "/".join([args.base_dir,case,args.arm,args.event])
        sys.exit(1)

    # Demographics from pipeline to grab case to scanner mapping
    demo_path = '/fs/ncanda-share/pipeline/summaries/redcap/demographics.csv'
    demographics = pd.read_csv(demo_path, index_col=['subject',
                                                     'arm',
                                                     'visit'])

    # gradient_map = dict(Siemens=get_ground_truth_gradients('Siemens',args.decimals), GE=get_ground_truth_gradients('GE',args.decimals))

    for case in cases:
        # Get the case's site
        dti_path = os.path.join(case, args.arm, args.event,'diffusion/native/dti60b1000')
        if not os.path.exists(dti_path) :
            if args.verbose:
                print "Warning: " + dti_path + " does not exist!"

            continue 

        if args.verbose:
            print "Processing: " + "/".join([case,args.arm, args.event])

        sid = os.path.basename(case)
        uploads += 1
        try:
            scanner = demographics.xs([sid, args.arm, args.event])['scanner']
            scanner_model = demographics.xs([sid, args.arm, args.event])['scanner_model']
        except :
            print "Error: case " + case + "," +  args.arm + "," + args.event +" not in " + demo_path +"!"
            continue

        if (isinstance(scanner, float) and math.isnan(scanner)) or (isinstance(scanner_model, float) and math.isnan(scanner_model)) :
            print "Error: Did not find scanner or model for " + sid + "/" +  args.arm + "/" + args.event +" so cannot check gradient for that scan!"
            continue

        xml_file_list = get_dti_stack(case, arm=args.arm, event=args.event)
        check_diffusion(dti_path,"",xml_file_list,scanner, scanner_model,args.decimals, post_to_github, time_log_dir)

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
                        default=2)
    parser.add_argument('-e', '--event', dest="event",
                        help="Study event. {}".format(default),
                        default='baseline')
    parser.add_argument('-c', '--case', dest="case",
                        help="Case to check - if none are defined then it checks all cases in that directory. {}".format(default), default=None)
    parser.add_argument('-v', '--verbose', dest="verbose",
                        help="Turn on verbose", action='store_true')
    parser.add_argument("-p", "--post-to-github", help="Post all issues to GitHub instead of std out.",
                        action="store_true")
    parser.add_argument("-t", "--time-log-dir",
                        help="If set then time logs are written to that directory (e.g. /fs/ncanda-share/ncanda-data-log/crond)",
                        action="store",
                        default=None)

    argv = parser.parse_args()

    # Setting up logging
    slog.init_log(argv.verbose, argv.post_to_github, 'NCANDA XNAT', 'check_gradient_tables', argv.time_log_dir)
    slog.startTimer1()

    sys.exit(main(argv))

slog.takeTimer1("script_time","{'records': " + str(len(records)) + ", 'uploads': " +  str(uploads) + "}")