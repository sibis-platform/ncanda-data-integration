#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2109 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:07:04 -0700 (Fri, 07 Aug 2015) $
##

import os
import time
import datetime

import pandas

#
# Behavior Rating Inventory of Executive Function (BRIEF)
#

input_fields = { 'youthreport2' : [ 'youthreport2_brief_sec1_brief1', 'youthreport2_brief_sec1_brief2', 'youthreport2_brief_sec1_brief3', 'youthreport2_brief_sec1_brief4', 
                                    'youthreport2_brief_sec1_brief5', 'youthreport2_brief_sec1_brief6', 'youthreport2_brief_sec1_brief7', 'youthreport2_brief_sec2_brief8', 
                                    'youthreport2_brief_sec2_brief9', 'youthreport2_brief_sec2_brief10', 'youthreport2_brief_sec2_brief11', 'youthreport2_brief_sec2_brief12', 
                                    'youthreport2_brief_sec2_brief13', 'youthreport2_brief_sec2_brief14', 'youthreport2_brief_sec3_brief15', 'youthreport2_brief_sec3_brief16', 
                                    'youthreport2_brief_sec3_brief17', 'youthreport2_brief_sec3_brief18', 'youthreport2_brief_sec3_brief19', 'youthreport2_brief_sec3_brief20', 
                                    'youthreport2_brief_sec3_brief21', 'youthreport2_brief_sec4_brief22', 'youthreport2_brief_sec4_brief23', 'youthreport2_brief_sec4_brief24', 
                                    'youthreport2_brief_sec4_brief25', 'youthreport2_brief_sec4_brief26', 'youthreport2_brief_sec4_brief27', 'youthreport2_brief_sec4_brief28', 
                                    'youthreport2_brief_sec5_brief29', 'youthreport2_brief_sec5_brief30', 'youthreport2_brief_sec5_brief31', 'youthreport2_brief_sec5_brief32', 
                                    'youthreport2_brief_sec5_brief33', 'youthreport2_brief_sec5_brief34', 'youthreport2_brief_sec5_brief35', 'youthreport2_brief_sec6_brief36', 
                                    'youthreport2_brief_sec6_brief37', 'youthreport2_brief_sec6_brief38', 'youthreport2_brief_sec6_brief39', 'youthreport2_brief_sec6_brief40', 
                                    'youthreport2_brief_sec6_brief41', 'youthreport2_brief_sec6_brief42', 'youthreport2_brief_sec7_brief43', 'youthreport2_brief_sec7_brief44', 
                                    'youthreport2_brief_sec7_brief45', 'youthreport2_brief_sec7_brief46', 'youthreport2_brief_sec7_brief47', 'youthreport2_brief_sec7_brief48', 
                                    'youthreport2_brief_sec7_brief49', 'youthreport2_brief_sec8_brief50', 'youthreport2_brief_sec8_brief51', 'youthreport2_brief_sec8_brief52', 
                                    'youthreport2_brief_sec8_brief53', 'youthreport2_brief_sec8_brief54', 'youthreport2_brief_sec8_brief55', 'youthreport2_brief_sec8_brief56', 
                                    'youthreport2_brief_sec9_brief57', 'youthreport2_brief_sec9_brief58', 'youthreport2_brief_sec9_brief59', 'youthreport2_brief_sec9_brief60', 
                                    'youthreport2_brief_sec9_brief61', 'youthreport2_brief_sec9_brief62', 'youthreport2_brief_sec9_brief63', 'youthreport2_brief_sec10_brief64',
                                    'youthreport2_brief_sec10_brief65', 'youthreport2_brief_sec10_brief66', 'youthreport2_brief_sec10_brief67', 'youthreport2_brief_sec10_brief68', 
                                    'youthreport2_brief_sec10_brief69', 'youthreport2_brief_sec10_brief70', 'youthreport2_brief_sec11_brief71', 'youthreport2_brief_sec11_brief72', 
                                    'youthreport2_brief_sec11_brief73', 'youthreport2_brief_sec11_brief74', 'youthreport2_brief_sec11_brief75', 'youthreport2_brief_sec11_brief76', 
                                    'youthreport2_brief_sec11_brief77', 'youthreport2_brief_sec12_brief78', 'youthreport2_brief_sec12_brief79', 'youthreport2_brief_sec12_brief80', 
                                    'youthreport2_date_interview' ] }

output_form = 'brief'

module_dir = os.path.dirname(os.path.abspath(__file__))

lookup_global = pandas.io.parsers.read_csv( os.path.join( module_dir, 'BRIEF_lookup_global_scales.csv' ), header=0, index_col=[0,1,2] )
lookup_subscales = pandas.io.parsers.read_csv( os.path.join( module_dir, 'BRIEF_lookup_subscales.csv' ), header=0, index_col=[0,1,2] )
lookup_index = pandas.io.parsers.read_csv( os.path.join( module_dir, 'BRIEF_lookup_index.csv' ), header=0, index_col=[0,1,2] )

# From the BRIEF VBA script - indexes the questions to the subscales
question_to_subscales = {   1: 1, 2: 3, 3: 6, 4: 7, 5: 4, 6: 8, 7: 5, 8: 9, 9: 2, 
                           10: 1, 11: 3, 12: 6, 13: 7, 14: 4, 15: 8, 16: 5, 17: 9, 18: 2, 19: 1, 
                           20: 9, 21: 6, 22: 7, 23: 4, 24: 8, 25: 5, 26: 9, 27: 2, 28: 1, 29: 7, 
                           30: 6, 31: 7, 32: 4, 33: 8, 34: 5, 35: 9, 36: 2, 37: 1, 38: 9, 39: 6, 
                           40: 7, 41: 4, 42: 8, 43: 5, 44: 9, 45: 2, 46: 1, 47: 7, 48: 6, 49: 7, 
                           50: 4, 51: 8, 52: 6, 53: 9, 54: 1, 55: 3, 56: 6, 57: 7, 58: 4, 59: 8, 
                           60: 7, 61: 1, 62: 3, 63: 6, 64: 7, 65: 4, 66: 1, 67: 3, 68: 6, 69: 7, 
                           70: 4, 71: 1, 72: 9, 73: 6, 74: 7, 75: 4, 76: 1, 77: 9, 78: 6, 79: 1, 
                           80: 1 }

# From the BRIEF VBA script - indexes the negativity questions
negativity_questions = [ 10, 11, 17, 19, 25, 30, 32, 43, 45, 54 ]

# From the BRIEF VBA script - indexes the inconsistency questions
inconsistency_questions = [ ( 8,26), (14,32), (20,77), (23,41), (38,72), (46,79), (55,67), (56,68), (58,65), (63,73) ]

# Score labels
labels = [ "", "brief_inhibit", "brief_beh_shift", "brief_cog_shift", "brief_control", "brief_monitor", "brief_memory", "brief_plan", "brief_materials", "brief_task", "brief_shift", "brief_bri", "brief_mi", "brief_gec" ]

def compute_scores( data, demographics ):
    # Eliminate all records with missing data
    data = data.dropna()

    # Initialize raw scores as 0
    for idx in range(1,11):
        data[ labels[idx]+'_raw' ] = 0

    for question, scale in question_to_subscales.iteritems():
        # Must add "+1" to each response because our scale is 0..2, whereas original BRIEF implementation is 1..3
        data[ labels[scale]+'_raw' ] = data[ labels[scale]+'_raw' ] + (1+data[ input_fields['youthreport2'][question-1] ])

    # Calculate summary raw scores
    data[ labels[10]+'_raw' ] = data[ labels[2]+'_raw' ] + data[ labels[3]+'_raw' ]
    data[ labels[11]+'_raw' ] = data[ labels[1]+'_raw' ] + data[ labels[10]+'_raw'] + data[ labels[4]+'_raw' ] + data[ labels[5]+'_raw' ]
    data[ labels[12]+'_raw' ] = data[ labels[6]+'_raw' ] + data[ labels[7]+'_raw' ] + data[ labels[8]+'_raw' ] + data[ labels[9]+'_raw' ]
    data[ labels[13]+'_raw' ] = data[ labels[11]+'_raw'] + data[ labels[12]+'_raw']

    # What is each subject's age at test?
    date_format_ymd = '%Y-%m-%d'
    data['brief_age'] = 0.0
    for key, row in data.iterrows():
        dob = demographics['dob'][key[0]]
        data['brief_age'][key] = (datetime.datetime.strptime( row['youthreport2_date_interview'], date_format_ymd ) - datetime.datetime.strptime( dob, date_format_ymd )).days / 365.242

    # Compute negativity
    data['brief_neg'] = 0
    for idx in range(1,11):
        # Have to count "2"s, because our scale is 0..2, whereas original implementation used scale 1..3
        data['brief_neg'] = data['brief_neg'] + data[ input_fields['youthreport2'][negativity_questions[idx-1]-1] ].map( lambda x: 1 if x==2 else 0 )
        
    # Compute inconsistency
    data['brief_incon'] = 0
    for idx in range(1,11):
        data['brief_incon'] = data['brief_incon'] + (data[ input_fields['youthreport2'][inconsistency_questions[idx-1][0]-1] ] - data[ input_fields['youthreport2'][inconsistency_questions[idx-1][1]-1] ]).abs()

    # Lookup from subscale
    for idx in range(1,11):
        data[ labels[idx]+'_t' ] = 0
        data[ labels[idx]+'_p' ] = 0
        for key, row in data.iterrows():
            sex = demographics['sex'][key[0]]
            lookup_key = ( 14 if row['brief_age'] < 15 else 15, 'F' if sex == 0 else 'M', row[ labels[idx]+'_raw' ] )
            data[ labels[idx]+'_t' ][key] = lookup_subscales[labels[idx]+'_t'][lookup_key]      
            data[ labels[idx]+'_p' ][key] = lookup_subscales[labels[idx]+'_p'][lookup_key]      

    for idx in range(11,13):
        data[ labels[idx]+'_t' ] = 0
        data[ labels[idx]+'_p' ] = 0
        for key, row in data.iterrows():
            sex = demographics['sex'][key[0]]
            lookup_key = ( 14 if row['brief_age'] < 15 else 15, 'F' if sex == 0 else 'M', row[ labels[idx]+'_raw' ] )
            data[ labels[idx]+'_t' ][key] = lookup_index[labels[idx]+'_t'][lookup_key]      
            data[ labels[idx]+'_p' ][key] = lookup_index[labels[idx]+'_p'][lookup_key]      

    data[ labels[13]+'_t' ] = 0
    data[ labels[13]+'_p' ] = 0
    for key, row in data.iterrows():
        sex = demographics['sex'][key[0]]
        lookup_key = ( 14 if row['brief_age'] < 15 else 15, 'F' if sex == 0 else 'M', row[ labels[13]+'_raw' ] )
        data[ labels[13]+'_t' ][key] = lookup_global[labels[13]+'_t'][lookup_key]      
        data[ labels[13]+'_p' ][key] = lookup_global[labels[13]+'_p'][lookup_key]      

    data['brief_complete'] = '1'

    return data[['%s_%s' % (label,score) for score in ['raw','t','p'] for label in labels if label != '']+['brief_age','brief_neg','brief_incon','brief_complete']]
