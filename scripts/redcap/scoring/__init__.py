#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import os
import glob
import stat
import sys
import imp
import hashlib
import pandas
from sibispy import sibislogger as slog

fields_list = dict()
functions = dict()
output_form = dict()
instrument_list = []

module_dir = os.path.dirname(os.path.abspath(__file__))

instruments = [ os.path.basename( d ) for d in glob.glob( os.path.join( module_dir, '*' ) ) if stat.S_ISDIR( os.stat( d ).st_mode ) and os.path.exists( os.path.join( d, '__init__.py' ) ) ]

sys.path.append( os.path.abspath( os.path.dirname( __file__ ) ) )

for i in instruments:
#    try:
        module_found = imp.find_module( i, [module_dir] )
        module = imp.load_module( i, module_found[0], module_found[1], module_found[2] )

        instrument_list.append( i )
        fields_list[i] =  module.input_fields
        functions[i] = module.compute_scores
        output_form[i] = module.output_form

def compute_scores(instrument,input_data,demographics):
    try:
        scoresDF = functions[instrument](input_data, demographics)   
    except Exception as e:
        error = "ERROR: scoring failed for instrument", instrument
        slog.info(instrument + "-" + hashlib.sha1(str(e)).hexdigest()[0:6], error, exception=str(e))
        return pandas.DataFrame()

    # remove nan entries as they corrupt data ingest (REDCAP cannot handle it correctly) and superfluous zeros
    # this gave an error as it only works for float values to replace
    if len(scoresDF) :
        # Only execute it not empty 
        return scoresDF.astype(object).fillna('')   
            
    return scoresDF

    # return scoresDF(lambda x: '' if math.isnan(x) else x )
