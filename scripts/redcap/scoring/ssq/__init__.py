#!/usr/bin/env python
 
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

#
# Variables from surveys needed for UPPS
#

input_fields = { 'youthreport2' : [ 'youth_report_2_complete', 'youthreport2_.*_ssq1bn' ] }
 

#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'

#
# Score one record by counting how many entry fields are non-empty (or, non-NaN, since we get these as floats)
# 
def score_ssq( row ):
    count_nonempty  = 0
    for field in ['youthreport2_ssq1b_1_ssq1bn', 'youthreport2_ssq1b_2_ssq1bn', 'youthreport2_ssq1b_3_ssq1bn', 'youthreport2_ssq1b_4_ssq1bn', 'youthreport2_ssq1b_5_ssq1bn',
                  'youthreport2_ssq1b_6_ssq1bn', 'youthreport2_ssq1b_7_ssq1bn', 'youthreport2_ssq1b_8_ssq1bn', 'youthreport2_ssq1b_9_ssq1bn' ]:
        entry = str( row[field] ).strip()
        if entry != '' and entry != 'nan':
            count_nonempty += 1
    return count_nonempty

#
# Scoring function - take requested data (as requested by "input_fields") for each (subject,event), and demographics (date of birth, gender) for each subject.
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have YR2
    data.dropna( axis=1, subset=['youth_report_2_complete'] )
    data = data[ data['youth_report_2_complete'] > 0 ]

    # Run the scoring function
    if len( data ) > 0:
        data['ssq_score'] = data.apply( score_ssq, axis=1 )
    else:
        data['ssq_score'] = ''

    # Simply copy completion status from the input surveys
    data['ssq_complete'] = data['youth_report_2_complete'].map( int )

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'ssq_score', 'ssq_complete' ]
    return data[ outfield_list ]

