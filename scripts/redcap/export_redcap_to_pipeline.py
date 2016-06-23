#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import os
import re
import glob
import time
import filecmp

import pandas


# Truncate age to 2 digits for increased identity protection
def truncate_age(age_in):
    match = re.match('([0-9]*\.[0-9]*)', str(age_in))
    if match:
        return round(float(match.group(1)), 2)
    else:
        return age_in


# "Safe" CSV export - this will catch IO errors from trying to write to a file
# that is currently being read and will retry a number of times before giving up
# This function will also confirm whether the newly created file is different
# from an already existing file of the same name. Only changed files will be
# updated.
def safe_csv_export(df, fname, verbose=False):
    success = False
    retries = 10

    while (not success) and (retries > 0):
        try:
            df.to_csv(fname + '.new', index=False)
            success = True
        except IOError as e:
            print "ERROR: failed to write file", fname, "with errno", e.errno
            if e.errno == 11:
                print "Retrying in 5s..."
                time.sleep(5)
                retries -= 1
            else:
                retries = 0

    if success:
        # Check if new file is equal to old file
        if os.path.exists(fname) and filecmp.cmp(fname, fname + '.new',
                                                 shallow=False):
            # Equal - remove new file
            os.remove(fname + '.new')
        else:
            # Not equal or no old file: put new file in its final place
            os.rename(fname + '.new', fname)

            if verbose:
                print "Updated", fname


# Export selected REDCap data to pipeline/distribution directory
def export(redcap_project, site, subject, event, subject_data, visit_age,
           visit_data, arm_code, visit_code, subject_code, subject_datadir,
           forms_this_event, select_exports=None, verbose=False):

    # Mark subjects/visits that have QA completed by creating a hidden marker
    # file
    qafile_path = os.path.join(subject_datadir, '.qacomplete')
    if visit_data['mri_qa_completed'] == '1':
        try:
            if not os.path.exists(qafile_path):
                qafile = open(qafile_path, 'w')
                qafile.close()
        except:
            print "ERROR: unable to open QA marker file in", subject_datadir
    else:
        try:
            if os.path.exists(qafile_path):
                os.remove(qafile_path)
        except:
            print "ERROR: unable to remove QA marker file", qafile_path

    # Check if the "measures" subdirectory already exists - this is where all
    # the csv files go. Create it if necessary.
    measures_dir = os.path.join(subject_datadir, 'measures')
    if not os.path.exists(measures_dir):
        os.makedirs(measures_dir)

    # Export demographics (if selected)
    if not select_exports or 'demographics' in select_exports:
        # Create "demographics" file "by hand" - this has some data not (yet)
        # in REDCap.

        # Latino and race coding arrives here as floating point numbers; make
        # int strings from that (cannot use "int()" because it would fail for
        # missing data
        hispanic_code = re.sub('(.0)|(nan)', '', str(subject_data['hispanic']))
        race_code = re.sub('(.0)|(nan)', '', str(subject_data['race']))

        # scanner manufacturer map
        mfg = dict(A='siemens', B='ge', C='ge', D='siemens', E='ge')

        demographics = [
            ['subject', subject_code],
            ['arm', arm_code],
            ['visit', visit_code],
            ['site', site],
            ['sex', subject[8]],
            ['visit_age', truncate_age(visit_age)],
            ['mri_structural_age', truncate_age(visit_data['mri_t1_age'])],
            ['mri_diffusion_age', truncate_age(visit_data['mri_dti_age'])],
            ['mri_restingstate_age',
             truncate_age(visit_data['mri_rsfmri_age'])],
            ['exceeds_bl_drinking',
             'NY'[int(subject_data['enroll_exception___drinking'])]],
            ['siblings_enrolled_yn',
             'NY'[int(subject_data['siblings_enrolled___true'])]],
            ['siblings_id_first', subject_data['siblings_id1']],
            ['hispanic', code_to_label_dict['hispanic'][hispanic_code][0:1]],
            ['race', race_code],
            ['race_label', code_to_label_dict['race'][race_code]],
            ['participant_id', subject],
            ['scanner', mfg[site]],
        ]

        if race_code == '6':
            # if other race is specified, mark race label with manually curated
            # race code
            demographics[14] = ('race_label', subject_data['race_other_code'])

        series = pandas.Series()
        for (key, value) in demographics:
            series = series.set_value(key, value)

        safe_csv_export(pandas.DataFrame(series).T,
                        os.path.join(measures_dir, 'demographics.csv'),
                        verbose=verbose)

    # First get data for all fields across all forms in this event - this speeds
    # up transfers over getting each form separately
    all_fields = ['study_id']
    export_list = []
    for export_name in export_forms.keys():
        if (import_forms[export_name] in forms_this_event) \
                and (not select_exports or export_name in select_exports):
            all_fields += [re.sub('___.*', '', field_name) for field_name in
                           export_forms[export_name]]
            export_list.append(export_name)

    all_records = redcap_project.export_records(fields=all_fields,
                                                records=[subject],
                                                events=[event],
                                                format='df')

    # Now go form by form and export data
    for export_name in export_list:
        # Remove the complete field from the list of forms
        complete = '{}_complete'.format(import_forms.get(export_name))
        fields = [column for column in export_forms.get(export_name)
                  if column != complete]

        # Select data for this form - "reindex_axis" is necessary to put
        # fields in listed order - REDCap returns them lexicographically sorted
        record = all_records[fields].reindex_axis(fields, axis=1)

        if len(record) == 1:
            # First, add the three index columns
            record.insert(0, 'subject', subject_code)
            record.insert(1, 'arm', arm_code)
            record.insert(2, 'visit', visit_code)

            field_idx = 0
            output_fields = []
            for field in record.columns:
                # Rename field for output if necessary
                if field in export_rename[export_name].keys():
                    output_field = export_rename[export_name][field]
                else:
                    output_field = field
                output_fields.append(output_field)

                # If this is an "age" field, truncate to 2 digits for privacy
                if re.match('.*_age$', field):
                    record[field] = record[field].apply(truncate_age)

                # If this is a radio or dropdown field
                # (except "FORM_[missing_]why"), add a separate column for the
                # coded label
                if field in code_to_label_dict.keys() and not re.match(
                        '.*_why$', field):
                    code = str(record[field].ix[0])
                    label = ''
                    if code in code_to_label_dict[field].keys():
                        label = code_to_label_dict[field][code]
                    field_idx += 1
                    record.insert(field_idx, output_field + '_label', label)
                    output_fields.append(output_field + '_label')

                field_idx += 1

            # Apply renaming to columns
            record.columns = output_fields

            # Figure out path for CSV file and export this record
            safe_csv_export(record,
                            os.path.join(measures_dir, export_name + '.csv'),
                            verbose=verbose)


# Filter potentially confidential fields out of given list, based on project
#  metadata
def filter_out_confidential(field_list, metadata_dict):
    filtered_list = []
    for field_name in field_list:
        try:
            (field_type, field_validation, field_label, text_val_min,
             text_val_max, choices) = metadata_dict[
                re.sub('___.*', '', field_name)]
            if (field_type != 'text' and field_type != 'notes') \
                    or (field_validation in ['number', 'integer', 'time']):
                filtered_list.append(field_name)
            else:
                print "WARNING: field '%s' is of type '%s' with " \
                      "validation '%s' - excluding as potentially " \
                      "confidential." % (field_name,
                                         field_type,
                                         field_validation)
        except:
            if '_complete' in field_name:
                filtered_list.append(field_name)

    return filtered_list

# Filter confidential fields from all forms
metadata_dict = dict()


def filter_all_forms(redcap_metadata):
    # First turn metadata into easily digested dict
    for field in redcap_metadata:
        field_tuple = (field['field_type'],
                       field['text_validation_type_or_show_slider_number'],
                       field['field_label'],
                       field['text_validation_min'],
                       field['text_validation_max'],
                       field['select_choices_or_calculations'])

        metadata_dict[field['field_name']] = field_tuple
    # Filter each form
    for export_name in export_forms.keys():
        export_forms[export_name] = filter_out_confidential(
            export_forms[export_name], metadata_dict)


# Make lookup dicts for mapping radio/dropdown codes to labels
code_to_label_dict = dict()


def make_code_label_dict(redcap_metadata):
    # First turn metadata into easily digested dict
    for field in redcap_metadata:
        if field['field_type'] in ['radio', 'dropdown']:
            field_dict = {'': ''}
            # Handle using sex from record id rather than datadict.
            if field['field_name'] == 'sex':
                choices = field['select_choices_or_calculations']
                choices.replace('0', 'F')
                choices.replace('1', 'M')
            else:
                choices = field['select_choices_or_calculations']
            for choice in choices.split('|'):
                code_label = [c.strip() for c in choice.split(',')]
                field_dict[code_label[0]] = ', '.join(code_label[1:])
            code_to_label_dict[field['field_name']] = field_dict


# Organize REDCap metadata (data dictionary)
def organize_metadata(redcap_metadata):
    filter_all_forms(redcap_metadata)
    make_code_label_dict(redcap_metadata)


# Create data dictionaries in a user-provided directory
# The columns in a REDCap data dictionary (MUST be in this order!!)

# for each entry in the form list you have to define a variable
def create_datadicts_general(datadict_dir, datadict_base_file,
                             export_forms_list, variable_list):
    redcap_datadict_columns = ["Variable / Field Name", "Form Name",
                               "Section Header", "Field Type", "Field Label",
                               "Choices, Calculations, OR Slider Labels",
                               "Field Note",
                               "Text Validation Type OR Show Slider Number",
                               "Text Validation Min", "Text Validation Max",
                               "Identifier?",
                               "Branching Logic (Show field only if...)",
                               "Required Field?", "Custom Alignment",
                               "Question Number (surveys only)",
                               "Matrix Group Name", "Matrix Ranking?"]

    if not os.path.exists(datadict_dir):
        os.makedirs(datadict_dir)

    ddict = pandas.DataFrame(index=variable_list,
                             columns=redcap_datadict_columns)

    for form_name, var in zip(export_forms_list, variable_list):
        field_name = re.sub('___.*', '', var)
        ddict["Variable / Field Name"][var] = field_name
        ddict["Form Name"][var] = form_name

        # Check if var is in data dict ('FORM_complete' fields are NOT)
        if field_name in metadata_dict.keys():
            ddict["Field Type"][var] = metadata_dict[field_name][0]
            # need to transfer to utf-8 code otherwise can create problems when
            # writing dictionary to file it just is a text field so it should
            #  not matter
            ddict["Field Label"][var] = metadata_dict[field_name][2].encode(
                'utf-8')
            ddict["Text Validation Type OR Show Slider Number"][var] = \
            metadata_dict[field_name][1]
            ddict["Text Validation Min"][var] = metadata_dict[field_name][3]
            ddict["Text Validation Max"][var] = metadata_dict[field_name][4]
            # need to transfer to utf-8 code otherwise can create problems when
            # writing dictionary to file it just is a choice field so it
            # should not matter
            ddict["Choices, Calculations, OR Slider Labels"][var] = \
            metadata_dict[field_name][5].encode('utf-8')

    # Finally, write the data dictionary to a CSV file
    dicFileName = os.path.join(datadict_dir,
                               datadict_base_file + '_datadict.csv')
    try:
        ddict.to_csv(dicFileName, index=False)
    except:
        import sys
        sys.exit(
            "ERROR:create_datadicts: could not export dictionary %s: \n%s:%s" %
            (dicFileName, sys.exc_info()[0].__doc__, sys.exc_info()[1]))


# defining entry_list only makes sense if export_forms_list only consists of one
# entry !
def create_datadicts(datadict_dir):
    # Go over all exported forms
    for export_name in export_forms.keys():
        export_form_entry_list = export_forms[export_name]
        size_entry_list = len(export_form_entry_list)
        export_form_list = [export_name] * size_entry_list
        create_datadicts_general(datadict_dir, export_name, export_form_list,
                                 export_form_entry_list)

    # Create custom form for demographics
    export_form_entry_list = ['site', 'sex', 'visit_age', 'mri_structural_age',
                              'mri_diffusion_age', 'mri_restingstate_age',
                              'exceeds_bl_drinking', 'siblings_enrolled_yn',
                              'siblings_id_first', 'hispanic', 'race',
                              'race_label', 'participant_id', 'scanner']

    # First two entries are extracted from SubjectID
    export_form_list = ['basic_demographics', 'basic_demographics',
                        'basic_demographics', 'mri_report', 'mri_report',
                        'mri_report', 'basic_demographics',
                        'basic_demographics', 'basic_demographics',
                        'basic_demographics', 'basic_demographics',
                        'basic_demographics', 'basic_demographics',
                        'basic_demographics']
    create_datadicts_general(datadict_dir, 'demographics', export_form_list,
                             export_form_entry_list)


#
# Initialization - figure out which instruments we're supposed to export, and
# which fields
#
import_forms = dict()
export_forms = dict()
export_names = dict()
export_rename = dict()

exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'exports')
exports_files = glob.glob(os.path.join(exports_dir, '*.txt'))
for f in exports_files:
    file = open(f, 'r')
    contents = [line.strip() for line in file.readlines()]
    file.close()

    export_name = re.sub('\.txt$', '', os.path.basename(f))

    import_form_name = re.sub('\n', '', contents[0])
    import_forms[export_name] = import_form_name
    export_forms[export_name] = [re.sub('\[.*\]', '', field) for field in
                                 contents[1:]] + [
                                    '%s_complete' % import_form_name]

    export_rename[export_name] = dict()
    for field in contents[1:]:
        match = re.match('^(.+)\[(.+)\]$', field)
        if match:
            export_rename[export_name][match.group(1)] = match.group(2)
