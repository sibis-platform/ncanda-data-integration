#!/usr/bin/env python
 
##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##

import pandas

import Rwrapper

#
# Variables from surveys needed for CTQ
#

# LimeSurvey field names
lime_fields = [ "ctq_set1 [ctq1]", "ctq_set1 [ctq2]", "ctq_set1 [ctq3]", "ctq_set1 [ctq4]", "ctq_set1 [ctq5]", "ctq_set1 [ctq6]", "ctq_set1 [ctq7]", "ctq_set2 [ctq8]", "ctq_set2 [ctq9]", "ctq_set2 [ct10]", "ctq_set2 [ct11]",
                "ctq_set2 [ct12]", "ctq_set2 [ct13]", "ctq_set2 [ct14]", "ctq_set3 [ctq15]", "ctq_set3 [ctq16]", "ctq_set3 [ctq17]", "ctq_set3 [ctq18]", "ctq_set3 [ctq19]", "ctq_set3 [ctq20]", "ctq_set3 [ctq21]",
                "ctq_set4 [ctq22]", "ctq_set4 [ctq23]", "ctq_set4 [ctq24]", "ctq_set4 [ctq25]", "ctq_set4 [ctq26]", "ctq_set4 [ctq27]", "ctq_set4 [ctq28]" ]

# Dictionary to recover LimeSurvey field names from REDCap names
rc2lime = dict()
for field in lime_fields:
    rc2lime[Rwrapper.label_to_sri( 'youthreport2', field )] = field

# REDCap fields names
input_fields = { 'mrireport' : [ 'youth_report_2_complete',  'youthreport2_missing' ] + rc2lime.keys() }

#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'

#
# CTQ field names mapping from R to REDCap
#
R2rc = { 'Emotional Abuse Scale Total Score' : 'ctq_ea', 
         'Physical Abuse Scale Total Score' : 'ctq_pa', 
         'Sexual Abuse Scale Total Score' : 'ctq_sa', 
         'Emotional Neglect Scale Total Score' : 'ctq_en', 
         'Physical Neglect Scale Total Score' : 'ctq_pn', 
         'Minimization/Denial Scale Total Score' : 'ctq_minds' }

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
    data.columns = Rwrapper.map_labels( data.columns, rc2lime )

    # Call the scoring function for all table rows
    scores = data.apply( Rwrapper.runscript, axis=1, Rscript='ctq/CTQ.R', scores_key='CTQ.ary' )

    # Replace all score columns with REDCap field names
    scores.columns = Rwrapper.map_labels( scores.columns, R2rc )

    # Simply copy completion status from the input surveys
    scores['ctq_complete'] = data['youth_report_2_complete'].map( int )

    # Make a proper multi-index for the scores table
    scores.index = pandas.MultiIndex.from_tuples(scores.index)
    scores.index.names = ['study_id', 'redcap_event_name']

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'ctq_complete' ] + R2rc.values()
    return scores[ outfield_list ]

