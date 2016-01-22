#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision$
##  $LastChangedBy$
##  $LastChangedDate$
##

import pandas
import string
import time
import datetime
import numpy

#
# High-Risk Status
#

# List of SSAGA variables to recode as: 1=>12, 2=>14, 3=>17, 4=>AGE
ssaga_recode_as_age = [ 'asa_ao2dk', 'asb_ao2dk', 'asc1_ao6dk', 'asc2_ao6dk', 'as_ao9dk', 'as_ao10dk', 'as1_ao11dk', 'as2_ao11dk', 'as1_ao15dk', 'as2_ao15dk', 'as1_ao16dk',
                        'as2_ao16dk', 'asa1_ao14dk', 'asa2_ao14dk', 'asc1_ao14dk', 'asc2_ao14dk', 'as1_ao17dk', 'as2_ao17dk', 'as1_ao19dk', 'as2_ao19dk', 'as1_ao18dk',
                        'as2_ao18dk', 'as1_ao20dk', 'as2_ao20dk' ]

ssaga_variables = ssaga_recode_as_age + [ 'complete', 'missing', 'dotest', 
                                          'al1ageons', 'as2a', 'asa_ao2', 'as2b', 'asb_ao2', 'as6b', 'asc1_ao6', 'asc2_ao6', 'as9', 'as_ao9', 
                                          'as10a', 'as_ao10', 'as11', 'as1_ao11', 'as2_ao11', 'as15', 'as1_ao15', 'as2_ao15', 'as16', 'as1_ao16', 'as2_ao16',
                                          'as14', 'asa1_ao14', 'asa2_ao14', 'as14b', 'asc1_ao14', 'asc2_ao14', 'as17a', 'as1_ao17', 'as2_ao17',
                                          'as19', 'as1_ao19', 'as2_ao19', 'as18b', 'as1_ao18', 'as2_ao18', 'as20', 'as1_ao20', 'as2_ao20',
                                          'oc1', 'oc_ao8', 'oc9', 'oc_ao16',
                                          'pn1x', 'pn2a', 'pn2b', 'pn5', 'pn_ao8', 'pn_ao8dk', 'pn_ao8dk',                                          
                                          'dp4a', 'dp4b', 'dp3', 'dp3_1', 'dp11', 'dp12', 'dp15a', 'dp15b', 'dp15c', 'dp15d' ]

input_fields = { 'youthreport1' : [ 'youthreport1_yfhi3a_yfhi3a', 'youthreport1_yfhi3a_yfhi3f', 'youthreport1_yfhi4a_yfhi4a', 'youthreport1_yfhi4a_yfhi4f',
                                    'youthreport1_yfhi3a_yfhi3b', 'youthreport1_yfhi4a_yfhi4b',
                                    'youthreport1_yfhi3a_yfhi3c', 'youthreport1_yfhi4a_yfhi4c', 
                                    'youthreport1_yfhi3a_yfhi3g', 'youthreport1_yfhi4a_yfhi4g', 
                                    'youthreport1_yfhi3a_yfhi3h', 'youthreport1_yfhi4a_yfhi4h',
                                    'youthreport1_date_interview', 'youth_report_1_complete', 'youthreport1_missing' ],
                 'parentreport' : [ 'parentreport_pfhi3a_pfhi3a', 'parentreport_pfhi3a_pfhi3f', 'parentreport_pfhi4a_pfhi4a', 'parentreport_pfhi4a_pfhi4f', 
                                    'parentreport_pfhi3a_pfhi3b', 'parentreport_pfhi4a_pfhi4b', 
                                    'parentreport_pfhi3a_pfhi3c', 'parentreport_pfhi4a_pfhi4c', 
                                    'parentreport_pfhi3a_pfhi3g', 'parentreport_pfhi4a_pfhi4g',
                                    'parentreport_pfhi3a_pfhi3h', 'parentreport_pfhi4a_pfhi4h',
                                    'parentreport_date_interview', 'parent_report_complete', 'parentreport_missing' ],
                 'ssaga_youth' : [ 'ssaga_youth_%s' % var for var in ssaga_variables ],
                 'ssaga_parent' : [ 'ssaga_parent_%s' % var for var in ssaga_variables ] }

output_form = 'highrisk'

#
# Recode one field as age
#
def recode_field_as_age( code, age ):
    if code == 1:
        return 12
    elif code == 2:
        return 14
    elif code == 3:
        return 17
    else:
        return age

#
# Compute the "parhx" variable
#
def compute_parhx( row ):
    have_youth_report = (row['youth_report_1_complete'] > 0) and not (row['youthreport1_missing'] > 0)
    have_parent_report = (row['parent_report_complete'] > 0) and not (row['parentreport_missing'] > 0)
    if have_youth_report or have_parent_report:
        parhx = 0
        if (have_youth_report and (row['youthreport1_yfhi3a_yfhi3a']==1 or row['youthreport1_yfhi4a_yfhi4a']==1)) or (have_parent_report and (row['parentreport_pfhi3a_pfhi3a']==1 or row['parentreport_pfhi4a_pfhi4a']==1)):
            parhx += 1
        
        if (have_youth_report and (row['youthreport1_yfhi3a_yfhi3f']==1 or row['youthreport1_yfhi4a_yfhi4f']==1)) or (have_parent_report and (row['parentreport_pfhi3a_pfhi3a']==1 or row['parentreport_pfhi4a_pfhi4f']==1)):
            parhx += 1

        return parhx
    else:
        return numpy.nan

#
# Compute the "gparhx" variable
#
def compute_gparhx( row ):
    have_youth_report = (row['youth_report_1_complete'] > 0) and not (row['youthreport1_missing'] > 0)
    have_parent_report = (row['parent_report_complete'] > 0) and not (row['parentreport_missing'] > 0)
    if have_youth_report or have_parent_report:
        gparhx = 0
        if (have_youth_report and (row['youthreport1_yfhi3a_yfhi3b']==1 or row['youthreport1_yfhi4a_yfhi4b']==1)) or (have_parent_report and (row['parentreport_pfhi3a_pfhi3b']==1 or row['parentreport_pfhi4a_pfhi4b']==1)):
            gparhx += 1
        
        if (have_youth_report and (row['youthreport1_yfhi3a_yfhi3c']==1 or row['youthreport1_yfhi4a_yfhi4c']==1)) or (have_parent_report and (row['parentreport_pfhi3a_pfhi3c']==1 or row['parentreport_pfhi4a_pfhi4c']==1)):
            gparhx += 1

        if (have_youth_report and (row['youthreport1_yfhi3a_yfhi3g']==1 or row['youthreport1_yfhi4a_yfhi4g']==1)) or (have_parent_report and (row['parentreport_pfhi3a_pfhi3g']==1 or row['parentreport_pfhi4a_pfhi4g']==1)):
            gparhx += 1

        if (have_youth_report and (row['youthreport1_yfhi3a_yfhi3h']==1 or row['youthreport1_yfhi4a_yfhi4h']==1)) or (have_parent_report and (row['parentreport_pfhi3a_pfhi3h']==1 or row['parentreport_pfhi4a_pfhi4h']==1)):
            gparhx += 1

        return gparhx
    else:
        return numpy.nan

#
# Compute the "extern" variable
#
def compute_extern( row, ssaga ):
    if (row['ssaga_%s_complete' % ssaga] > 0) and not (row['ssaga_%s_missing' % ssaga] > 0):
        # First extract the fields for this particular SSAGA into an easy-to-query dictionary
        this_ssaga = dict()
        for var in ssaga_variables:
            this_ssaga[var] = row['ssaga_%s_%s' % (ssaga,var)]
        age_onset = this_ssaga['al1ageons']

        if age_onset == numpy.nan:
            return numpy.nan

        extern = 0
        if this_ssaga['as2a']==5 and min( this_ssaga['asa_ao2'], this_ssaga['asa_ao2dk'] ) < age_onset:
            extern += 1

        if this_ssaga['as2b']==5 and min( this_ssaga['asb_ao2'], this_ssaga['asb_ao2dk'] ) < age_onset:
            extern += 1
            
        if this_ssaga['as6b'] > 1 and min( this_ssaga['asc1_ao6'], this_ssaga['asc2_ao6'], this_ssaga['asc1_ao6dk'], this_ssaga['asc2_ao6dk'] ) < age_onset:
            extern += 1

        if this_ssaga['as9']==5 and min( this_ssaga['as_ao9'], this_ssaga['as_ao9dk']) < age_onset:
            extern += 1

        if this_ssaga['as10a'] > 1 and min( this_ssaga['as_ao10'], this_ssaga['as_ao10dk'] ) < age_onset:
            extern += 1

        if this_ssaga['as11'] > 1 and min( this_ssaga['as1_ao11'], this_ssaga['as2_ao11'], this_ssaga['as1_ao11dk'], this_ssaga['as2_ao11dk'] ) < age_onset:
            extern += 1
        
        if this_ssaga['as15'] > 1 and min( this_ssaga['as1_ao15'], this_ssaga['as2_ao15'], this_ssaga['as1_ao15dk'], this_ssaga['as2_ao15dk'] ) < age_onset:
            extern += 1

        if this_ssaga['as16'] > 1 and min( this_ssaga['as1_ao16'], this_ssaga['as2_ao16'], this_ssaga['as1_ao16dk'], this_ssaga['as2_ao16dk'] ) < age_onset:
            extern += 1

        # The next check is an "and" of two longer expressions; implement this as nested if's for readability
        if this_ssaga['as14'] > 1 and min( this_ssaga['asa1_ao14'], this_ssaga['asa2_ao14'], this_ssaga['asa1_ao14dk'], this_ssaga['asa2_ao14dk'] ) < age_onset:
            if this_ssaga['as14b'] > 1 and min( this_ssaga['asc1_ao14'], this_ssaga['asc2_ao14'], this_ssaga['asc1_ao14dk'], this_ssaga['asc2_ao14dk'] ) < age_onset:
                extern += 1

        if this_ssaga['as17a'] == 5 and min( this_ssaga['as1_ao17'], this_ssaga['as2_ao17'], this_ssaga['as1_ao17dk'], this_ssaga['as2_ao17dk'] ) < age_onset:
            extern += 1
            
        if this_ssaga['as19'] > 1 and min( this_ssaga['as1_ao19'], this_ssaga['as2_ao19'], this_ssaga['as1_ao19dk'], this_ssaga['as2_ao19dk'] ) < age_onset:
            extern += 1

        if this_ssaga['as18b'] == 5 and min( this_ssaga['as1_ao18'], this_ssaga['as2_ao18'], this_ssaga['as1_ao18dk'], this_ssaga['as2_ao18dk'] ) < age_onset:
            extern += 1
                
        if this_ssaga['as20'] > 1 and min( this_ssaga['as1_ao20'], this_ssaga['as2_ao20'], this_ssaga['as1_ao20dk'], this_ssaga['as2_ao20dk'] ) < age_onset:
            extern += 1
        
        return extern

    return numpy.nan

#
# Call "extern" computation for Youth SSAGA
#
def compute_extern_youth( row ):
    return compute_extern( row, 'youth' )

#
# Call "extern" computation for Parent SSAGA
#
def compute_extern_parent( row ):
    return compute_extern( row, 'parent' )

#
# Compute the "intern" variable
#
def compute_intern( row, ssaga ):
    if (row['ssaga_%s_complete' % ssaga] > 0) and not (row['ssaga_%s_missing' % ssaga] > 0):
        # First extract the fields for this particular SSAGA into an easy-to-query dictionary
        this_ssaga = dict()
        for var in ssaga_variables:
            this_ssaga[var] = row['ssaga_%s_%s' % (ssaga,var)]
        age_onset = this_ssaga['al1ageons']
            
        if age_onset == numpy.nan:
            return numpy.nan

        intern = 0
            
        if this_ssaga['oc1']==5 and (this_ssaga['oc_ao8'] < age_onset):
            intern += 1
            
        if this_ssaga['oc9']==5 and (this_ssaga['oc_ao16'] < age_onset):
            intern += 1

        if (this_ssaga['pn1x']==5 or this_ssaga['pn2a']==5 or this_ssaga['pn2b']==5 or this_ssaga['pn5'] > 2) and ((this_ssaga['pn_ao8'] < age_onset) or (this_ssaga['pn_ao8dk']==1 and age_onset > 10) or (this_ssaga['pn_ao8dk']==2 and age_onset > 20)):
            intern += 1

        dp3_age_check = (this_ssaga['dp3'] < age_onset) or (this_ssaga['dp3_1']==1 and age_onset > 10) or (this_ssaga['dp3_1']==2 and age_onset > 20)
        if (this_ssaga['dp4a']==5 or this_ssaga['dp4b']==5) and dp3_age_check:
            intern += 1

        if (this_ssaga['dp11']==5 or this_ssaga['dp12']==5) and dp3_age_check:
            intern += 1
            
        if (this_ssaga['dp15a']==5 or this_ssaga['dp15b']==5 or this_ssaga['dp15c']==5 or this_ssaga['dp15d']==5) and dp3_age_check:
            intern += 1

        return intern

    return numpy.nan

#
# Call "intern" computation for Youth SSAGA
#
def compute_intern_youth( row ):
    return compute_intern( row, 'youth' )

#
# Call "intern" computation for Parent SSAGA
#
def compute_intern_parent( row ):
    return compute_intern( row, 'parent' )

#
# Compute risk status for one row (i.e., one record)
#
def compute_status( row ):
    status = 0

    if row['highrisk_gparhx'] > 1 or row['highrisk_parhx'] > 1:
        status = 1

    if (row['ssaga_youth_complete'] and not (row['ssaga_youth_missing'] > 0) and (row['ssaga_youth_al1ageons'] <= 14)):
        status = 1

    if (row['ssaga_parent_complete'] and not (row['ssaga_parent_missing'] > 0) and (row['ssaga_parent_al1ageons'] <= 14)):
        status = 1

    if row['highrisk_yss_intern'] > 2 or row['highrisk_pss_intern'] > 2:
        status = 1

    if row['highrisk_yss_extern'] > 2 or row['highrisk_pss_extern'] > 2:
        status = 1

    return status

#
# Driver function - go through the steps of status determination
#
def compute_scores( data, demographics ):
    outfield_list = [ 'highrisk_parhx', 'highrisk_gparhx', 
                      'highrisk_yss_intern', 'highrisk_yss_extern', 'highrisk_yss_al1ageons', 
                      'highrisk_pss_intern', 'highrisk_pss_extern', 'highrisk_pss_al1ageons', 
                      'highrisk_status', 'highrisk_complete' ]
    for outfield in outfield_list:
        data[outfield] = 0

    # First, for each SSAGA (Youth and Parent) determine subject age and re-code age-related fields according to lookup table
    date_format_ymd = '%Y-%m-%d'
    for key, row in data.iterrows():
        try:
            dob = datetime.datetime.strptime( demographics['dob'][key[0]], date_format_ymd )
            for ssaga in ['youth','parent']:
                if (row['ssaga_%s_complete' % ssaga] > 0) and not (row['ssaga_%s_missing' % ssaga] > 0):
                    try:
                        age = (datetime.datetime.strptime( row['ssaga_%s_dotest' % ssaga], date_format_ymd ) - dob).days / 365.242
                    except:
                        #Old Printing method
                        #print 'WARNING: Problem parsing',ssaga,'SSAGA date',row['ssaga_%s_dotest' % ssaga],'for subject',key[0],row['ssaga_%s_record_id'%ssaga]
                        error = dict(subject_id=key[0],
                                 ssage=ssage,
                                 ssaga_date=row['ssaga_%s_dotest' % ssaga],
                                 error='WARNING: Problem parsing.')
                        print(json.dumps(error, sort_keys=True))
                    age = numpy.nan
                    for column in ssaga_recode_as_age:
                        fieldname = 'ssaga_%s_%s' % (ssaga,var)
                        data[fieldname][key] = recode_field_as_age( data[fieldname][key], age )
        except:
            #Old Printing Method
            #print 'WARNING: Problem determining DOB for subject',key[0]
            error = dict(subject_id = key[0],
                         error = 'WARNING: Problem determining DOB for subject')
            for column in ssaga_recode_as_age:
                for ssaga in ['youth','parent']:
                    fieldname = 'ssaga_%s_%s' % (ssaga,var)
                    data[fieldname][key] = numpy.nan

    # Second, compute "parhx" and "gparhx" from youth and/or parent repor
    data['highrisk_parhx'] = data.apply( compute_parhx, axis=1 )
    data['highrisk_gparhx'] = data.apply( compute_gparhx, axis=1 )

    # Third, compute "internalizing" from Youth and/or Parent SSAGA
    data['highrisk_yss_intern'] = data.apply( compute_intern_youth, axis=1 )
    data['highrisk_pss_intern'] = data.apply( compute_intern_parent, axis=1 )

    # Fourth, compute "exterrnalizing" from Youth and/or Parent SSAGA
    data['highrisk_yss_extern'] = data.apply( compute_extern_youth, axis=1 )
    data['highrisk_pss_extern'] = data.apply( compute_extern_parent, axis=1 )    

    # Fifth, compute composite "risk status"
    data['highrisk_status'] = data.apply( compute_status, axis=1 )

    # Sixth, for good measure, copy the "Age of Onset" columns from the two SSAGA instruments
    data['highrisk_yss_al1ageons'] = data['ssaga_youth_al1ageons']
    data['highrisk_pss_al1ageons'] = data['ssaga_parent_al1ageons']

    # Finally, convert everything to strings (and nan to emptry string) to avoid validation errors
    for outfield in outfield_list:
        data[outfield] = data[outfield].map( lambda x: str(int(x)) if str(x) != 'nan' else '' )

    data['highrisk_complete'] = '1'
    return data[ outfield_list ]
