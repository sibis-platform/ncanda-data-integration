#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##


import pandas
import string
import time
import datetime
import numpy
import numpy as np

input_fields = { 'cnp_summary' : [ 'cnp_cpfd_dfac_tot', # CPFD Total Correct Responses
                                    'cnp_cpfd_dfac_rtc',# CPFD Median Total Correct Response Time
                                    'cnp_cpwd_dwrd_tot',# CPWD Total Correct Responses
                                    'cnp_cpwd_dwrd_rtc',# Median Response Time for CPWD Total Correct Responses  
                                    'cnp_summary_complete', 'cnp_missing' ] }

output_form = 'clinical'
#outfield_list = ['cnp_cpfd_eff_cpfd','cnp_cpwd_eff_cpwd','cnp_complete' ]
outfield_list = ['cnp_cpfd_eff_cpfd','cnp_cpwd_eff_cpwd','cnp_eff_complete' ]

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
    eff_cpfd = np.nan
    eff_cpwd = np.nan
    
    # check cnp_summary
    if (record['cnp_summary_complete'] > 0) and ( record['cnp_missing'] !=  1 ): 
      	if (safe_float( record['cnp_cpfd_dfac_tot']) > 0 and (safe_float( record['cnp_cpfd_dfac_rtc'] ) > 0)):
            eff_cpfd = safe_float( record['cnp_cpfd_dfac_rtc'] )
	    eff_cpfd = np.log(eff_cpfd)
	    eff_cpfd = safe_float( record['cnp_cpfd_dfac_tot'] )/eff_cpfd
        if (safe_float( record['cnp_cpwd_dwrd_tot']) > 0):
            eff_cpwd = safe_float( record['cnp_cpwd_dwrd_rtc'] )
	    eff_cpwd = np.log(eff_cpwd)
	    eff_cpwd = safe_float( record['cnp_cpwd_dwrd_tot'] )/eff_cpwd
        record['cnp_eff_complete'] =  str(int(safe_float(record['cnp_summary_complete'])))
	record['cnp_cpfd_eff_cpfd'] = eff_cpfd
	record['cnp_cpwd_eff_cpwd'] = eff_cpwd
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
