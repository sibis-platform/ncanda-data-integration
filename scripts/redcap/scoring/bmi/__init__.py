#!/usr/bin/env python

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##

import os
import string
import time

import numpy
import pandas

input_fields = { 'youthreport1' : [ 'youthreport1_cddrheight', # Height in inches
                                    'youthreport1_cddrweight', # Weight in pounds
                                    'youthreport1_age',
                                    'youth_report_1_complete', 'youthreport1_missing', 'youthreport1_date' ] }

output_form = 'clinical'

outfield_list = [ 'bmi_value', 'bmi_zscore', 'bmi_percentile', 'bmi_complete' ]

#
# Read Lookup Table
#  The table was obtained on August 1, 2014 from http://www.cdc.gov/growthcharts/percentile_data_files.htm
#

module_dir = os.path.dirname(os.path.abspath(__file__))
bmi_lookup_table = pandas.io.parsers.read_csv( os.path.join( module_dir, 'bmiagerev.csv' ), header=0 )
bmi_lookup_table = bmi_lookup_table[ [ 'Sex', 'Agemos', 'L', 'M', 'S' ] ]

#
# Computation function
#

def compute( record, demographics ):
    X = record['bmi_value']

    # Select the part of the lookup table for the correct sex (REDCap is 0=F/1=M; table is 1=M/2=F)
    sex = demographics['sex'][record.name[0]]
    if sex == 0:
        sex = 2
    lookup_table_sex = bmi_lookup_table[ bmi_lookup_table['Sex'] == sex ]
    
    # Sort lookup table rows by difference between actual and tabulated age, then take first row (closest age)
    age_months = record['youthreport1_age'] * 12
    lookup_table_sex['dAge'] = (lookup_table_sex['Agemos'] - age_months).map( abs )
    lookup_row = lookup_table_sex.sort( columns = 'dAge', inplace = False ).irow(0)

    (L,M,S) = (lookup_row['L'],lookup_row['M'],lookup_row['S'])

    z_score = ( pow(X/M,L) - 1) / (L*S)
    return z_score

#
# Driver function - go through the steps of status determination
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have YR1
    data.dropna( axis=1, subset=['youth_report_1_complete'] )
    data = data[ data['youth_report_1_complete'] > 0 ]
    data = data[ ~(data['youthreport1_missing'] > 0) ]

    # If no records to score, return empty DF
    if len( data ) == 0:
        return pandas.DataFrame()
    data['bmi_complete'] = data['youth_report_1_complete']

    # Convert height and weight to m and kg, respectively
    data['youthreport1_cddrheight'] = data['youthreport1_cddrheight'] * .0254
    data['youthreport1_cddrweight'] = data['youthreport1_cddrweight'] * 0.453592

    # Compute BMI
    data['bmi_value'] = data['youthreport1_cddrweight'] / ( data['youthreport1_cddrheight'] * data['youthreport1_cddrheight'] )

    # Do computations, return result
    data['bmi_zscore'] = data.apply( compute, axis=1, demographics=demographics )

    from scipy.stats import norm
    data['bmi_percentile'] = data['bmi_zscore'].map( norm.cdf ) * 100

    return data[outfield_list]
