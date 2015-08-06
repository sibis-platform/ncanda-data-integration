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
##  $Revision$
##
##  $LastChangedDate$
##
##  $LastChangedBy$
##

fields_list = dict()
functions = dict()
output_form = dict()
instrument_list = []

import os
module_dir = os.path.dirname(os.path.abspath(__file__))

import glob
import stat
instruments = [ os.path.basename( d ) for d in glob.glob( os.path.join( module_dir, '*' ) ) if stat.S_ISDIR( os.stat( d ).st_mode ) and os.path.exists( os.path.join( d, '__init__.py' ) ) ]

import sys
sys.path.append( os.path.abspath( os.path.dirname( __file__ ) ) )

import imp
for i in instruments:
#    try:
        module_found = imp.find_module( i, [module_dir] )
        module = imp.load_module( i, module_found[0], module_found[1], module_found[2] )

        instrument_list.append( i )
        fields_list[i] =  module.input_fields
        functions[i] = module.compute_scores
        output_form[i] = module.output_form
#    except:
#        sys.exit( "ERROR: could not import scoring module '%s'" % i )
