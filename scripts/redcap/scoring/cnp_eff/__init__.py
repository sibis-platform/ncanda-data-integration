#!/usr/bin/env python

##
##  Copyright 2013, 2014 SRI International
##
##  http://nitrc.org/projects/ncanda-datacore/
##
##  This file is part of the N-CANDA Data Component Software Suite, developed
##  and distributed by the Data Integration Component of the National
##  Consortium on Alcohol and NeuroDevelopment in Adolescence, supported by
##  the U.S. National Institute on Alcohol Abuse and Alcoholism (NIAAA) under
##  Grant No. 1U01 AA021697
##
##  The N-CANDA Data Component Software Suite is free software: you can
##  redistribute it and/or modify it under the terms of the GNU General Public
##  License as published by the Free Software Foundation, either version 3 of
##  the License, or (at your option) any later version.
##
##  The N-CANDA Data Component Software Suite is distributed in the hope that it
##  will be useful, but WITHOUT ANY WARRANTY; without even the implied
##  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with the N-CANDA Data Component Software Suite.  If not, see
##  <http://www.gnu.org/licenses/>.
##
##  $Revision: 1410 $
##
##  $LastChangedDate: 2014-05-20 11:37:58 -0700 (Tue, 20 May 2014) $
##
##  $LastChangedBy: torstenrohlfing $
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
