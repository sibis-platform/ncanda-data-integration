#!/usr/bin/env python
 
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import re
import pandas
import math
from sibispy import utils as sutils

#
# Variables from surveys needed for PSQI
#

# LimeSurvey field names
lime_fields = [ "psqi1", "psqi2", "psqi3", "psqi4", "psqi_set1 [psqi5a]", "psqi_set1 [psqi5b]", "psqi_set1 [psqi5c]", "psqi_set1 [psqi5d]", "psqi_set1 [psqi5e]", "psqi_set2 [psqi5f]", "psqi_set2 [psqi5g]", "psqi_set2 [psqi5h]",
                "psqi_set2 [psqi5i]", "psqi5j", "psqi5jc", "psqi6", "psqi_set3 [psqi7]", "psqi_set3 [psqi8]", "psqi9" ]

# Dictionary to recover LimeSurvey field names from REDCap names
rc2lime = dict()
for field in lime_fields:
    rc2lime[sutils.label_to_limesurvey_to_redcap( 'youthreport2', field )] = field

# REDCap fields names
input_fields = { 'youthreport2' : [ 'youth_report_2_complete',  'youthreport2_missing' ] + rc2lime.keys() }

#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'

#
# PSQI field names mapping from R to REDCap
#
R2rc = { 'PSQI' : 'psqi_total' }
for field in [ 'PSQIDURAT', 'PSQIDISTB', 'PSQILATEN' ,'PSQIDAYDYS', 'PSQIHSE', 'PSQISLPQUAL', 'PSQIMEDS' ]:
    R2rc[field] = re.sub( 'psqi', 'psqi_', field.lower() )

#
# Scoring function - take requested data (as requested by "input_fields") for each (subject,event), and demographics (date of birth, gender) for each subject.
#

def compute_scores( data, demographics ):
    # Get rid of all records that don't have YR2
    data.dropna( axis=0, subset=['youth_report_2_complete'] )
    data = data[ data['youth_report_2_complete'] > 0 ]
    data = data[ ~(data['youthreport2_missing'] > 0) ]

    # If no records to score, return empty DF
    if len( data ) == 0:
        return pandas.DataFrame()

    # Replace all column labels with the original LimeSurvey names
    data.columns = sutils.map_labels_to_dict( data.columns, rc2lime )

    # Call the scoring function for all table rows
    scores = data.apply( sutils.run_rscript, axis=1, Rscript='psqi/PSQI.R' )

    # Replace all score columns with REDCap field names
    scores.columns = sutils.map_labels_to_dict( scores.columns, R2rc )

    # Simply copy completion status from the input surveys
    scores['psqi_complete'] = data['youth_report_2_complete'].map( int )

    # Make a proper multi-index for the scores table
    scores.index = pandas.MultiIndex.from_tuples(scores.index)
    scores.index.names = ['study_id', 'redcap_event_name']

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'psqi_complete' ] + R2rc.values()

    returnDF= scores[ outfield_list ]
    # remove nan entries as they corrupt data ingest (REDCAP cannot handle it correctly) and superfluous zeros as these should all be integer scores 
    return returnDF.applymap(lambda x: '' if math.isnan(x) else '{0:g}'.format(float(x)))
