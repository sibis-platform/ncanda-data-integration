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
import string
import time
import datetime
import numpy

input_fields = { 'parentreport' : [ 'parentreport_sesp3', # highest grade you has completed
                                    'parentreport_sesp3b',# highest grade you has completed
                                    'parentreport_sesp14',# TOTAL COMBINED FAMILY INCOME categories                      
                                    'parent_report_complete', 'parentreport_missing' ] }

output_form = 'clinical'
outfield_list = [ 'ses_parent_score', 'ses_parent_faminc', 'ses_parent_yoe', 'ses_complete' ]

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
    # check parent report
    if (record['parent_report_complete'] > 0) and ( record['parentreport_missing'] != 1 ):
	edu_valid = False
	income_valid = False

        # Get max education and check if valid (many are missing)
        edu = max( [ safe_float( record['parentreport_sesp3'] ), safe_float( record['parentreport_sesp3b'] ) ] )
	if edu > 0:
            record['ses_parent_yoe'] = int( edu )
            edu_valid = True

        # Get family income and make sure it's not "don't know"
        income = safe_float( record['parentreport_sesp14'] )
	if (income > 0) and (income < 11): ## '11' is "Don't know!"
            record['ses_parent_faminc'] = int( income )
            income_valid = True

        # Score valid only if both education and income are known
        if edu_valid and income_valid:
	    record['ses_parent_score'] = int( edu*3+income*5 )

        # Only set "Complete" status if not "missing"
        record['ses_complete'] =  str( record['parent_report_complete'] )

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
