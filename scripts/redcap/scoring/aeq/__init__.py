#!/usr/bin/env python
 
##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##

import re
import pandas

import RwrapperNew

#
# Variables from surveys needed for AEQ
#

# LimeSurvey field names
lime_fields = [ "AEQ_sec1 [aeq1]", "AEQ_sec1 [aeq2]", "AEQ_sec1 [aeq3]", "AEQ_sec1 [aeq4]", "AEQ_sec1 [aeq5]", "AEQ_sec1 [aeq6]", "AEQ_sec1 [aeq7]", "AEQ_sec2 [aeq8]", "AEQ_sec2 [aeq9]","AEQ_sec2 [aeq10]", "AEQ_sec2 [aeq11]", 
                "AEQ_sec2 [aeq12]", "AEQ_sec2 [aeq13]", "AEQ_sec2 [aeq14]", "AEQ_sec3 [aeq15]", "AEQ_sec3 [aeq16]", "AEQ_sec3 [aeq17]", "AEQ_sec3 [aeq18]", "AEQ_sec3 [aeq19]", "AEQ_sec3 [aeq20]", "AEQ_sec3 [aeq21]" ]

# Dictionary to recover LimeSurvey field names from REDCap names
rc2lime = dict()
for field in lime_fields:
    rc2lime[RwrapperNew.label_to_sri( 'youthreport2', field )] = field

# REDCap fields names
input_fields = { 'youthreport2' : [ 'youth_report_2_complete',  'youthreport2_missing' ] + rc2lime.keys() }

#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'

#
# AEQ field names mapping from R to REDCap
#
R2rc = dict()
for field in [ 'AEQ.GPC', 'AEQ.CSB', 'AEQ.ICMA', 'AEQ.SE', 'AEQ.CMI', 'AEQ.IA', 'AEQ.RTR', 'AEQ.MEAN', 'AEQ.POS', 'AEQ.NEG' ]:
    R2rc[field] = re.sub( '\.', '_', field.lower() )

#
# Scoring function - take requested data (as requested by "input_fields") for each (subject,event), and demographics (date of birth, gender) for each subject.
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have YR2
    data.dropna( axis=1, subset=['youth_report_2_complete'] )
    data = data[ data['youth_report_2_complete'] > 0 ]
    data = data[ ~(data['youthreport2_missing'] > 0) ]

    # If no records to score, return empty DF
    if len( data ) == 0:
        return pandas.DataFrame()

    # Replace all column labels with the original LimeSurvey names
    data.columns = RwrapperNew.map_labels( data.columns, rc2lime )

    # Call the scoring function for all table rows
    scores = data.apply( RwrapperNew.runscript, axis=1, Rscript='aeq/AEQ.R' )

    # Replace all score columns with REDCap field names
    scores.columns = RwrapperNew.map_labels( scores.columns, R2rc )

    # Simply copy completion status from the input surveys
    scores['aeq_complete'] = data['youth_report_2_complete'].map( int )

    # Make a proper multi-index for the scores table
    scores.index = pandas.MultiIndex.from_tuples(scores.index)
    scores.index.names = ['study_id', 'redcap_event_name']

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'aeq_complete' ] + R2rc.values()
    return scores[ outfield_list ]

