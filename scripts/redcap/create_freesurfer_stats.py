#!/usr/bin/env python
"""

"""
import os
import re
import sys

import pandas as pd


def read_stats(filename):
    """Convert a FreeSurfer stats file to a structure.

    Args:
        filename (str): Path to a FreeSurfer stats file.

    Returns:
        A dictionary containing the provenance, data dictionary, and measures.

    """
    header = {}
    tableinfo = {}
    measures = []
    with open(filename, 'rt') as fp:
        lines = fp.readlines()
    for line in lines:
        if line == line[0]:
            continue
        # parse commented header
        if line.startswith('#'):
            fields = line.split()[1:]
            if len(fields) < 2:
                continue
            tag = fields[0]
            if tag == 'TableCol':
                col_idx = int(fields[1])
                if col_idx not in tableinfo:
                    tableinfo[col_idx] = {}
                tableinfo[col_idx][fields[2]] = ' '.join(fields[3:])
                if tableinfo[col_idx][fields[2]] == "StructName":
                    struct_idx = col_idx
            elif tag == "Measure":
                fields = ' '.join(fields[1:]).split(', ')
                measures.append({'structure': fields[0],
                                 'name': fields[1],
                                 'description': fields[2],
                                 'value': fields[3],
                                 'units': fields[4],
                                 'source': 'Header'})
            elif tag == "ColHeaders":
                if len(fields) != len(tableinfo):
                    for idx, fieldname in enumerate(fields[1:]):
                        if idx + 1 in tableinfo:
                            continue
                        tableinfo[idx + 1] = {'ColHeader': fieldname,
                                              'Units': 'unknown',
                                              'FieldName': fieldname}
                else:
                    continue
            else:
                header[tag] = ' '.join(fields[1:])
        else:
            # read values
            row = line.split()
            measures.append({'structure': row[struct_idx-1],
                             'items': [],
                             'source': 'Table'}),
            for idx, value in enumerate(row):
                if idx + 1 == struct_idx:
                    continue
                measures[-1]['items'].append({
                    'name': tableinfo[idx + 1]['ColHeader'],
                    'description': tableinfo[idx + 1]['FieldName'],
                    'value': value,
                    'units': tableinfo[idx + 1]['Units']})
    return dict(prov=header, datadict=tableinfo, measures=measures)


def create_datadict(parsed_stats):
    """Create a data dictionary in REDCap format.

    Args:
        parsed_stats (dict): The result from read_stats.

    Returns:
        A pandas.DataFrame in REDCap data dictionary format.

    """
    # Get the form name.
    prov = parsed_stats.get('prov')
    if prov.get('generating_program') == 'mri_segstats':
        form_name = 'aseg_stats'
    elif prov.get('generating_program') == 'mris_anatomical_stats':
        annot = os.path.basename(prov.get('AnnotationFile'))
        stats = annot.replace('.annot', '.stats')
        form_name = stats.replace('.', '_')
    else:
        form_name = 'stats'
    datadict = parsed_stats.get('datadict')
    rows = list()
    for idx in datadict:
        row_template = get_datadict_template()
        row = datadict.get(idx)
        field = row.get('ColHeader')
        row_template.update(
            {"Variable / Field Name": camel_to_underscore(field),
             "Form Name": form_name,
             "Field Label": row.get('FieldName'),
             "Field Note": row.get('Units')})
        rows.append(row_template)
    return pd.DataFrame(rows, columns=get_columns())


def get_columns():
    """Get list of REDCap datadict columns.

    Returns:
        A list of REDCap datadict columns.
    """
    columns = ["Variable / Field Name",
               "Form Name",
               "Section Header",
               "Field Type",
               "Field Label",
               "Choices, Calculations, OR Slider Labels",
               "Field Note",
               "Text Validation Type OR Show Slider Number",
               "Text Validation Min",
               "Text Validation Max",
               "Identifier?",
               "Branching Logic (Show field only if...)",
               "Required Field?",
               "Custom Alignment",
               "Question Number (surveys only)",
               "Matrix Group Name",
               "Matrix Ranking?",
               "Field Annotation"]
    return columns


def get_datadict_template():
    """Get a REDCap format datadict template.

    Returns:
        A dict prepopulated with keys in REDCap format.

    """
    return {column: "" for column in get_columns()}


def camel_to_underscore(name):
    """Convert from camel case to underscore.

    Args:
        name (str): camel case or any string.

    Returns:
        A string with underscores.
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def main(args=None):
    parsed_stats = read_stats(args.infile)
    datadict = create_datadict(parsed_stats)
    datadict.to_csv('~/Downloads/datadict.csv', index=False)

if __name__ == "__main__":
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="create_freesurfer_stats.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('-i', '--infile',
                        required=True,
                        help='Input stats file from freesurfer.')
    argv = parser.parse_args()
    sys.exit(main(args=argv))
