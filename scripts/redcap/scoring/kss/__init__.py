#!/usr/bin/env python
 
##
##  Copyright 2013-2014 SRI International
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
##  $Revision$
##
##  $LastChangedDate$
##
##  $LastChangedBy$
##

#
# Variables from surveys needed for KSS
#

input_fields = { 'mrireport' : [ 'mri_report_complete', 'mrireport_missing', 'mrireport_kss01_1', 'mrireport_kss02_1' ] }
 
#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'
 
#
# Scoring function - KSS really just copies the survey responses
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have MRI Report
    data.dropna( axis=1, subset=['mri_report_complete'] )
    data = data[ data['mri_report_complete'] > 0 ]
    data = data[ ~(data['mrireport_missing'] > 0) ]

    data['kss_mri_before'] = data['mrireport_kss01_1']
    data['kss_mri_after'] = data['mrireport_kss02_1']
    data['kss_complete'] = data['mri_report_complete'].map( int )

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'kss_complete', 'kss_mri_before', 'kss_mri_after' ]
    return data[ outfield_list ]

