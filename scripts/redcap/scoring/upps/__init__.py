#!/usr/bin/env python
 
##
##  Copyright 2013 SRI International
##
##  http://nitrc.org/projects/ncanda-datacore/
##
##  This file is part of the N-CANDA Data Component Software Suite, developed
##  and distributed by the Data Integration Component of the National
##  Consortium on Alcohol and NeuroDevelopment in Adolescence, supported by
##  the U.S. National Institute on Alcohol Abuse and Alcoholism (NIAAA) under
##  Grant No. 1U01 AA021697
##
##  The N-CANDA Data Component Software Suite is free software: you can
##  redistribute it and/or modify it under the terms of the GNU General Public
##  License as published by the Free Software Foundation, either version 3 of
##  the License, or (at your option) any later version.
##
##  The N-CANDA Data Component Software Suite is distributed in the hope that it
##  will be useful, but WITHOUT ANY WARRANTY; without even the implied
##  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with the N-CANDA Data Component Software Suite.  If not, see
##  <http://www.gnu.org/licenses/>.
##
##  $Revision$
##
##  $LastChangedDate$
##
##  $LastChangedBy$
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

