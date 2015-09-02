#!/usr/bin/env python
 
##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2109 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:07:04 -0700 (Fri, 07 Aug 2015) $
##

import pandas

import Rwrapper

#
# Variables from surveys needed for HSS
#

# LimeSurvey field names
lime_fields = [ "Hssweek_sec1 [hssweek2]", "Hssweek_sec1 [hssweek3]", "Hssweek_sec1 [hssweek4]", "Hssweek_sec1 [hssweek5]", "Hssweek_sec1 [hssweek6]", "Hssweek_sec1 [hssweek7]", "Hssweek_sec1 [hssweek8]", "Hssweek_sec2 [hssweek9]",
                "Hssweek_sec2 [hssweek10]", "Hssweek_sec2 [hssweek11]", "Hssweek_sec2 [hssweek12]", "Hssweek_sec2 [hssweek13]", "Hssweek_sec2 [hssweek14]",
                "hssyear_sec1 [hssyear2]", "hssyear_sec1 [hssyear3]", "hssyear_sec1 [hssyear4]", "hssyear_sec1 [hssyear5]", "hssyear_sec1 [hssyear6]", "hssyear_sec1 [hssyear7]", "hssyear_sec2 [hssyear8]", "hssyear_sec2 [hssyear9]",
                "hssyear_sec2 [hssyea10]", "hssyear_sec2 [hssyea11]", "hssyear_sec2 [hssyea12]", "hssyear_sec2 [hssyea13]", "hssyear_sec2 [hssyea14]" ]

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
# HSS field names mapping from R to REDCap
#
R2rc = { 'HSS Past Week Score' : 'hss_pastweek', 'HSS Past Year Score' : 'hss_pastyear' }

#
# Scoring function - take requested data (as requested by "input_fields") for each (subject,event), and demographics (date of birth, gender) for each subject.
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have MRI Report
    data.dropna( axis=1, subset=['youth_report_2_complete'] )
    data = data[ data['youth_report_2_complete'] > 0 ]
    data = data[ ~(data['youthreport2_missing'] > 0) ]

    # If no records to score, return empty DF
    if len( data ) == 0:
        return pandas.DataFrame()

    # Replace all column labels with the original LimeSurvey names
    data.columns = Rwrapper.map_labels( data.columns, rc2lime )

    # Call the scoring function for all table rows
    scores = data.apply( Rwrapper.runscript, axis=1, Rscript='hss/HSS.R', scores_key='HSS.ary' )

    # Replace all score columns with REDCap field names
    scores.columns = Rwrapper.map_labels( scores.columns, R2rc )

    # Simply copy completion status from the input surveys
    scores['hss_complete'] = data['youth_report_2_complete'].map( int )

    # Make a proper multi-index for the scores table
    scores.index = pandas.MultiIndex.from_tuples(scores.index)
    scores.index.names = ['study_id', 'redcap_event_name']

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'hss_complete' ] + R2rc.values()
    return scores[ outfield_list ]

