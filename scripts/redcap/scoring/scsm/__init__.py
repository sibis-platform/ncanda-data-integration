#!/usr/bin/env python
 
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

#
# Variables from surveys needed for SCSM
#

input_fields = { 'youthreport2' : [ 'youth_report_2_complete', 'youthreport2_missing', 'youthreport2_scsm1', 'youthreport2_scsm2', 'youthreport2_scsm3', 'youthreport2_scsm4', 'youthreport2_scsm5', 'youthreport2_scsm6',
                                    'youthreport2_scsm7', 'youthreport2_scsm8', 'youthreport2_scsm9', 'youthreport2_scsm10', 'youthreport2_scsm11', 'youthreport2_scsm12', 'youthreport2_scsm13' ] }
 
#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'

#
# Scoring function - SCSM really just copies a survey response
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have YR2
    data.dropna( axis=1, subset=['youth_report_2_complete'] )
    data = data[ data['youth_report_2_complete'] > 0 ]
    data = data[ ~(data['youthreport2_missing'] > 0) ]

    data['scsm_score'] = 6-data['youthreport2_scsm1'] + 6-data['youthreport2_scsm2'] + data['youthreport2_scsm3'] + data['youthreport2_scsm4'] + data['youthreport2_scsm5']+5 - data['youthreport2_scsm6'] + 6-data['youthreport2_scsm7'] + 5-data['youthreport2_scsm8'] + 5-data['youthreport2_scsm9'] + 5-data['youthreport2_scsm10']+ data['youthreport2_scsm11'] + 5-data['youthreport2_scsm12'] + 5-data['youthreport2_scsm13']

    data['scsm_complete'] = data['youth_report_2_complete'].map( int )

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'scsm_complete', 'scsm_score' ]
    return data[ outfield_list ]

