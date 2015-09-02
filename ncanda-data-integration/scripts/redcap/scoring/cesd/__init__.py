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
# Variables from surveys needed for CES-D
#

# LimeSurvey field names
lime_fields = [ "cesd_sec1 [cesd1]", "cesd_sec1 [cesd2]", "cesd_sec1 [cesd3]", "cesd_sec1 [cesd4]", "cesd_sec1 [cesd5]", "cesd_sec1 [cesd6]", "cesd_sec2 [cesd7]", "cesd_sec2 [cesd8]", "cesd_sec2 [cesd9]", "cesd_sec2 [ces10]",
                "cesd_sec2 [ces11]", "cesd_sec2 [ces12]", "cesd_sec3 [ces13]", "cesd_sec3 [ces14]", "cesd_sec3 [ces15]", "cesd_sec3 [ces16]", "cesd_sec3 [ces17]", "cesd_sec3 [ces18]", "cesd_sec3 [ces19]", "cesd_sec3 [ces20]" ]

# Dictionary to recover LimeSurvey field names from REDCap names
rc2lime = dict()
for field in lime_fields:
    rc2lime[Rwrapper.label_to_sri( 'mrireport', field )] = field

# REDCap fields names
input_fields = { 'mrireport' : [ 'mri_report_complete',  'mrireport_missing' ] + rc2lime.keys() }

#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'

#
# CES-D field names mapping from R to REDCap
#
R2rc = { 'CES Symptomatology Score' : 'cesd_score' }

#
# Scoring function - take requested data (as requested by "input_fields") for each (subject,event), and demographics (date of birth, gender) for each subject.
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have MRI Report
    data.dropna( axis=1, subset=['mri_report_complete'] )
    data = data[ data['mri_report_complete'] > 0 ]
    data = data[ ~(data['mrireport_missing'] > 0) ]

    # If no records to score, return empty DF
    if len( data ) == 0:
        return pandas.DataFrame()

    # Replace all column labels with the original LimeSurvey names
    data.columns = Rwrapper.map_labels( data.columns, rc2lime )

    # Call the scoring function for all table rows
    scores = data.apply( Rwrapper.runscript, axis=1, Rscript='cesd/CES_D.R', scores_key='CES.ary' )

    # Replace all score columns with REDCap field names
    scores.columns = Rwrapper.map_labels( scores.columns, R2rc )

    # Simply copy completion status from the input surveys
    scores['cesd_complete'] = data['mri_report_complete'].map( int )

    # Make a proper multi-index for the scores table
    scores.index = pandas.MultiIndex.from_tuples(scores.index)
    scores.index.names = ['study_id', 'redcap_event_name']

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'cesd_complete' ] + R2rc.values()
    return scores[ outfield_list ]

