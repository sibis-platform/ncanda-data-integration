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

import re
import tempfile
import subprocess
import shutil
import os.path
import pandas

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
def runscript( row, Rscript=None ):
    tmpdir = tempfile.mkdtemp()

    data_csv = os.path.join( tmpdir, 'data.csv' )
    scores_csv = os.path.join( tmpdir, 'scores.csv' )

    pandas.DataFrame( row ).T.to_csv( data_csv )

    module_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        Routput = subprocess.check_output( [ '/usr/bin/Rscript', os.path.join( module_dir, Rscript ), data_csv, scores_csv ],stderr=subprocess.STDOUT )
    except subprocess.CalledProcessError as e:
        print "R failed with error",e
        print Routput
        return

    scores = pandas.read_csv( scores_csv, index_col=None )
    shutil.rmtree( tmpdir )

    return scores.ix[0]
