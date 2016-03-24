#!/usr/bin/env python
 
##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##

#
# Variables from surveys needed for SISE
#

input_fields = { 'youthreport2' : [ 'youth_report_2_complete', 'youthreport2_missing', 'youthreport2_sise' ] }
 
#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'
 
#
# Scoring function - SISE really just copies a survey response
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have YR2
    data.dropna( axis=1, subset=['youth_report_2_complete'] )
    data = data[ data['youth_report_2_complete'] > 0 ]
    data = data[ ~(data['youthreport2_missing'] > 0) ]

    data['sise_score'] = data['youthreport2_sise']
    data['sise_complete'] = data['youth_report_2_complete'].map( int )

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'sise_complete', 'sise_score' ]
    return data[ outfield_list ]

