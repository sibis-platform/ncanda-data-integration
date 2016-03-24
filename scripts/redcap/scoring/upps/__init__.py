#!/usr/bin/env python
 
##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##

#
# Variables from surveys needed for UPPS
#

input_fields = { 'youthreport2' : [ 'youth_report_2_complete',
                                    'youthreport2_upps_sec1_upps4', 'youthreport2_upps_sec1_upps5', 'youthreport2_upps_sec1_upps10', 'youthreport2_upps_sec1_upps14', 'youthreport2_upps_sec1_upps16',
                                    'youthreport2_upps_sec2_upps17', 'youthreport2_upps_sec2_upps19', 'youthreport2_upps_sec2_upps20', 'youthreport2_upps_sec2_upps22', 'youthreport2_upps_sec2_upps23',
                                    'youthreport2_upps_sec3_upps27', 'youthreport2_upps_sec3_upps28', 'youthreport2_upps_sec3_upps29', 'youthreport2_upps_sec3_upps31', 'youthreport2_upps_sec3_upps34',
                                    'youthreport2_upps_sec4_upps35', 'youthreport2_upps_sec4_upps36', 'youthreport2_upps_sec4_upps46', 'youthreport2_upps_sec4_upps48', 'youthreport2_upps_sec4_upps52' ] }
 
#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'
 
#
# Scoring function - take requested data (as requested by "input_fields") for each (subject,event), and demographics (date of birth, gender) for each subject.
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have YR2
    data.dropna( axis=1, subset=['youth_report_2_complete'] )
    data = data[ data['youth_report_2_complete'] > 0 ]

    data['upps_nug'] = (5-data['youthreport2_upps_sec2_upps17']+5-data['youthreport2_upps_sec2_upps22']+data['youthreport2_upps_sec3_upps29']+data['youthreport2_upps_sec3_upps34'])/4     # Negative Urgency
    data['upps_psv'] = (data['youthreport2_upps_sec1_upps4']+data['youthreport2_upps_sec1_upps14']+data['youthreport2_upps_sec2_upps19']+data['youthreport2_upps_sec3_upps27'])/4          # Perseverance
    data['upps_pmt'] = (data['youthreport2_upps_sec1_upps5']+5-data['youthreport2_upps_sec1_upps16']+data['youthreport2_upps_sec3_upps28']+data['youthreport2_upps_sec4_upps48'])/4        # Premeditation
    data['upps_sss'] = (5-data['youthreport2_upps_sec2_upps23']+5-data['youthreport2_upps_sec3_upps31']+5-data['youthreport2_upps_sec4_upps36']+5-data['youthreport2_upps_sec4_upps46'])/4 # Sensation Seeking
    data['upps_pug'] = (5-data['youthreport2_upps_sec1_upps10']+5-data['youthreport2_upps_sec2_upps20']+5-data['youthreport2_upps_sec4_upps35']+5-data['youthreport2_upps_sec4_upps52'])/4 # Positive Urgency

    data['upps_complete'] = data['youth_report_2_complete'].map( int )

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'upps_nug', 'upps_psv' ,'upps_pmt', 'upps_sss' ,'upps_pug', 'upps_complete' ]
    return data[ outfield_list ]

