#!/usr/bin/env python

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##

import pandas
import string
import time
import datetime
import numpy

input_fields = { 'youthreport1' : [ 'youthreport1_ydi6', # number of full siblings in same household
                                    'youthreport1_ydi7', # number of half/step/adopted siblings in same household
                                    'youthreport1_yfhi1_yfhi1a', # number of pat uncles
                                    'youthreport1_yfhi1_yfhi1b', # number of pat aunts
                                    'youthreport1_yfhi2_yfhi2a', # number of mat uncles
                                    'youthreport1_yfhi2_yfhi2b', # number of mat aunts
                                    'youthreport1_yfhi4a_yfhi4a', # bio dad > 2 problems
                                    'youthreport1_yfhi4a_yfhi4b', # pat grandpa
                                    'youthreport1_yfhi4a_yfhi4c', # pat grandma
                                    'youthreport1_yfhi4a_yfhi4f', # bio mom                                   
                                    'youthreport1_yfhi4a_yfhi4g', # mat grandpa
                                    'youthreport1_yfhi4a_yfhi4h', # mat grandma
                                    'youthreport1_yfhi4b_yfhi4d_1', # pat uncles w > 2 problems
                                    'youthreport1_yfhi4b_yfhi4e_1', # pat aunts
                                    'youthreport1_yfhi4b_yfhi4i_1', # mat uncles
                                    'youthreport1_yfhi4b_yfhi4j_1', # mat aunts
                                    'youthreport1_yfhi4b_yfhi4k_1', # younger siblings
                                    'youthreport1_yfhi4b_yfhi4l_1', # older siblings
                                    'youth_report_1_complete', 'youthreport1_missing' ],
                 'parentreport' : [ 'parentreport_pfhi1_pfhi1a', # number of pat uncles
                                    'parentreport_pfhi1_pfhi1b', # number of pat aunts
                                    'parentreport_pfhi2_pfhi2a', # number of mat uncles
                                    'parentreport_pfhi2_pfhi2b', # number of mat aunts
                                    'parentreport_pfhi4a_pfhi4a', # bio dad > 2 problems
                                    'parentreport_pfhi4a_pfhi4b', # pat grandpa
                                    'parentreport_pfhi4a_pfhi4c', # pat grandma
                                    'parentreport_pfhi4a_pfhi4f', # bio mom                                   
                                    'parentreport_pfhi4a_pfhi4g', # mat grandpa
                                    'parentreport_pfhi4a_pfhi4h', # mat grandma
                                    'parentreport_pfhi4b_pfhi4d_1', # pat uncles w > 2 problems
                                    'parentreport_pfhi4b_pfhi4d_1', # pat aunts
                                    'parentreport_pfhi4b_pfhi4i_1', # mat uncles
                                    'parentreport_pfhi4b_pfhi4j_1', # mat aunts
                                    'parentreport_pfhi4b_pfhi4k_1', # younger siblings
                                    'parentreport_pfhi4b_pfhi4l_1', # older siblings                                    
                                    'parent_report_complete', 'parentreport_missing' ] }

output_form = 'clinical'
outfield_list = [ 'fh_drug', 'fh_drug_density', 'fh_drug_complete' ]

#
# Safe conversion of string to float
#
def safe_float( strng ):
    if strng == '' or str( strng ) == 'nan':
        return 0
    try:
        return float( strng )
    except:
        return 0

#
# Computation function
#
def compute( record ):
    first_degree = None
    second_degree = None

    # check youth report first
    if (record['youth_report_1_complete'] > 0) and ( 'youthreport1_missing' != '1' ):
        first_degree = safe_float( record['youthreport1_yfhi4b_yfhi4k_1'] ) + safe_float( record['youthreport1_yfhi4b_yfhi4l_1'] )
        for f in ['youthreport1_yfhi4a_yfhi4a', 'youthreport1_yfhi4a_yfhi4f']:
            if record[f] == '1':
                first_degree += 1
                
        second_degree = safe_float( record['youthreport1_yfhi4b_yfhi4d_1'] ) + safe_float( record['youthreport1_yfhi4b_yfhi4e_1'] ) + safe_float( record['youthreport1_yfhi4b_yfhi4i_1'] ) + safe_float( record['youthreport1_yfhi4b_yfhi4j_1'] )
        for f in ['youthreport1_yfhi4a_yfhi4b', 'youthreport1_yfhi4a_yfhi4c', 'youthreport1_yfhi4a_yfhi4g', 'youthreport1_yfhi4a_yfhi4h']:
            if record[f] == '1':
                second_degree += 1

        record['fh_drug_complete'] = str( record['youth_report_1_complete'] )

    # check parent report second
    if (record['parent_report_complete'] > 0) and ( 'parentreport_missing' != '1' ):
        first_degree_pr = safe_float( record['parentreport_pfhi4b_pfhi4k_1'] ) + safe_float( record['parentreport_pfhi4b_pfhi4l_1'] )
        for f in ['parentreport_pfhi4a_pfhi4a', 'parentreport_pfhi4a_pfhi4f']:
            if record[f] == '1':
                first_degree_pr += 1
                
        second_degree_pr = safe_float( record['parentreport_pfhi4b_pfhi4d_1'] ) + safe_float( record['parentreport_pfhi4b_pfhi4d_1'] ) + safe_float( record['parentreport_pfhi4b_pfhi4i_1'] ) + safe_float( record['parentreport_pfhi4b_pfhi4j_1'] )
        for f in ['parentreport_pfhi4a_pfhi4b', 'parentreport_pfhi4a_pfhi4c', 'parentreport_pfhi4a_pfhi4g', 'parentreport_pfhi4a_pfhi4h']:
            if record[f] == '1':
                second_degree_pr += 1

        # Check against youth-reported relatives; use higher number
        if (first_degree == None) or (first_degree_pr > first_degree):
            first_degree = first_degree_pr
        if (second_degree == None) or (second_degree_pr > second_degree):
            second_degree = second_degree_pr

        if record['fh_drug_complete'] == '':
            record['fh_drug_complete'] = str( record['parent_report_complete'] )

    # Make classification based on maximum of youth/parent reported relative counts
    if (record['fh_drug_complete'] != ''):
        if ( first_degree != None ) and ( second_degree != None ):
            if ( first_degree >= 1 or second_degree >= 2 ):
                record['fh_drug'] = 'P'
            else:
                record['fh_drug'] = 'N'
            record['fh_drug_density'] = first_degree + 0.5 * second_degree

    return record[ outfield_list ]

#
# Driver function - go through the steps of status determination
#
def compute_scores( data, demographics ):
    for f in outfield_list:
        data[f] = ''

    # Do computations, return result
    results = data.apply( compute, axis=1 )
    results.index = pandas.MultiIndex.from_tuples( results.index )
    return results
