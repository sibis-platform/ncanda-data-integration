#!/usr/bin/env python
 
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import pandas

import Rwrapper

#
# Variables from surveys needed for TIPI
#

# LimeSurvey field names
lime_fields = [ "TIPI_sec1 [tipi1]", "TIPI_sec1 [tipi2]", "TIPI_sec1 [tipi3]", "TIPI_sec1 [tipi4]", "TIPI_sec1 [tipi5]", "TIPI_sec2 [tipi6]", "TIPI_sec2 [tipi7]", "TIPI_sec2 [tipi8]", "TIPI_sec2 [tipi9]", "TIPI_sec2 [tipi10]" ]

# Dictionary to recover LimeSurvey field names from REDCap names
rc2lime = dict()
for field in lime_fields:
    rc2lime[Rwrapper.label_to_sri( 'youthreport2', field )] = field

# REDCap fields names
input_fields = { 'youthreport2' : [ 'youth_report_2_complete',  'youthreport2_missing' ] + rc2lime.keys() }

#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'

#
# TIPI field names mapping from R to REDCap
#
R2rc = { 'Agreeableness' : 'tipi_agv', 'Conscientiousness' : 'tipi_csv', 'Emotional Stability' : 'tipi_ems', 'Extraversion' : 'tipi_etv', 'Openness to Experiences' : 'tipi_ope' }

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
    scores = data.apply( Rwrapper.runscript, axis=1, Rscript='tipi/TIPI.R', scores_key='TIPI.ary' )

    # Replace all score columns with REDCap field names
    scores.columns = Rwrapper.map_labels( scores.columns, R2rc )

    # Simply copy completion status from the input surveys
    scores['tipi_complete'] = data['youth_report_2_complete'].map( int )

    # Make a proper multi-index for the scores table
    scores.index = pandas.MultiIndex.from_tuples(scores.index)
    scores.index.names = ['study_id', 'redcap_event_name']

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'tipi_complete' ] + R2rc.values()
    return scores[ outfield_list ]

