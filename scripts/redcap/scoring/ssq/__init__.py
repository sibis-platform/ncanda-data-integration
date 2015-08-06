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

