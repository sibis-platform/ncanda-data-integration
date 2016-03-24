#!/usr/bin/env python
 
##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##

import re
import pandas

import RwrapperNew

#
# Variables from surveys needed for PDS
#

# LimeSurvey field names
lime_fields = [ "pdsf1", "pdsf2", "pdsf3", "pdsf4", "pdsf5a", "pdsf5b",
                "pdsm1", "pdsm2", "pdsm3", "pdsm4", "pdsm5" ]

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
# PDS field names mapping from R to REDCap
#
R2rc = { 'PDSS' : 'pds_score', 'pubcat' : 'pds_pubcat' }

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

    # Set "ydi2" ("sex" field in LimeSurvey) based on what is in REDCap - this is chacked against subject ID  and should avoid mis-entered data
    data['ydi2'] = data.index.map( lambda key: demographics['sex'][key[0]] )
    
    # Replace all column labels with the original LimeSurvey names
    data.columns = RwrapperNew.map_labels( data.columns, rc2lime )

    # Call the scoring function for all table rows
    scores = data.apply( RwrapperNew.runscript, axis=1, Rscript='pds/PDS.R' )

    # Replace all score columns with REDCap field names
    scores.columns = RwrapperNew.map_labels( scores.columns, R2rc )

    # Simply copy completion status from the input surveys
    scores['pds_complete'] = data['youth_report_2_complete'].map( int )

    # Make a proper multi-index for the scores table
    scores.index = pandas.MultiIndex.from_tuples(scores.index)
    scores.index.names = ['study_id', 'redcap_event_name']

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'pds_complete' ] + R2rc.values()
    return scores[ outfield_list ]

