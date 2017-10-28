#!/usr/bin/env python
 
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import re
import tempfile
import shutil
import os.path
import pandas
from sibispy import utils as sutils

# Label translation function - LimeSurvey to SRI/old REDCap style
def label_to_sri( prefix, ls_label ):
    return "%s_%s" % (prefix, re.sub( '_$', '', re.sub( '[_\W]+', '_', re.sub( 'subjid', 'subject_id', ls_label.lower() ) ) ) )

# Map labels in a list according to a dictionary
def map_labels( labels, ldict ):
    new_labels = list()
    for label in labels:
        if label in ldict.keys():
            new_labels.append( ldict[label] )
        else:
            new_labels.append( label )
    return new_labels

# Score one record by running R script
def runscript( row, Rscript=None, scores_key=None ):
    tmpdir = tempfile.mkdtemp()

    data_csv = os.path.join( tmpdir, 'data.csv' )
    scores_csv = os.path.join( tmpdir, 'scores.csv' )

    pandas.DataFrame( row ).T.to_csv( data_csv )

    module_dir = os.path.dirname(os.path.abspath(__file__))

    (errcode, stdout, stderr) = sutils.Rscript(str(os.path.join( module_dir, Rscript )) + " " +  data_csv + " " scores_csv)
    if errcode : 
        print "R failed with error", stderr
        print stdout
        return
        
    scores = pandas.read_csv( scores_csv, index_col=None )
    shutil.rmtree( tmpdir )
    if scores_key : 
        return pandas.Series( name = row.name, data = scores.to_dict()[scores_key] )
    else : 
        return scores.ix[0]
