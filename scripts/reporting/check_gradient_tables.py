#!/usr/bin/en python
import os
import glob

import numpy as np
from lxml import objectify

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
    strip_dicom = strip_ge.replace('dicom:','')
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

def get_cases(cases_root, case=None):
    """
    Get a list of cases from root dir, optionally for a single case
    """
    match = 'NCANDA_S*'
    if case:
        match = case
    return glob.glob(os.path.join(cases_root, match))

def get_dti_stack(case, arm=None, event=None):
  if arm:
    path = os.path.join(case, arm)
  else:
    path = os.path.join(case, '*')
  if event:
    path = os.path.join(path, event)
  else:
    path = os.path.join(path,'*')

  path = os.path.join(path, 'diffusion/native/dti60b1000/*.xml')
  return glob.glob(path)

def get_all_gradients(dti_stack, decimals=None):
    """
    Parses a list of dti sidecar files for subject.

    Returns
    =======
    list of np.array
    """
    gradiets_per_frame = list()
    for xml in dti_stack:
        sidecar = read_xml_sidecar(xml)
        gradiets_per_frame.append(get_gradient_table(sidecar,
                                                     decimals=decimals))
    return gradiets_per_frame


# Using NCANDA_S00033 as ground truth
path = '/fs/ncanda-share/pipeline/cases'
case = 'NCANDA_S00033'
arm = 'standard'
event = 'baseline'

dti_path = os.path.join(path, case)
dti_stack = get_dti_stack(dti_path, arm=arm, event=event)
gradients = get_all_gradients(dti_stack, decimals=1)

# Get the gradient tables for all cases and compare to ground truth
results = dict()
for case in get_cases(path):
    print("Processing: {}...".format(case))
    case_dti = os.path.join(path, case)
    case_stack = get_dti_stack(dti_path, arm=arm, event=event)
    case_gradients = get_all_gradients(case_stack, decimals=1)
    errors = list()
    for idx, frame in enumerate(case_gradients):
        # if there is a frame that doesn't match, report it.
        if not (gradients[idx]==frame).all():
            errors.append(idx)
    if errors:
        key = '-'.join([case, arm, event])
        results.update({key: errors})
        print("Error: {}...".format(results))
