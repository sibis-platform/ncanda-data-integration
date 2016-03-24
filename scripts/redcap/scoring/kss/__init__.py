#!/usr/bin/env python
 
##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##

#
# Variables from surveys needed for KSS
#

input_fields = { 'mrireport' : [ 'mri_report_complete', 'mrireport_missing', 'mrireport_kss01_1', 'mrireport_kss02_1' ] }
 
#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'
 
#
# Scoring function - KSS really just copies the survey responses
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have MRI Report
    data.dropna( axis=1, subset=['mri_report_complete'] )
    data = data[ data['mri_report_complete'] > 0 ]
    data = data[ ~(data['mrireport_missing'] > 0) ]

    data['kss_mri_before'] = data['mrireport_kss01_1']
    data['kss_mri_after'] = data['mrireport_kss02_1']
    data['kss_complete'] = data['mri_report_complete'].map( int )

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'kss_complete', 'kss_mri_before', 'kss_mri_after' ]
    return data[ outfield_list ]

