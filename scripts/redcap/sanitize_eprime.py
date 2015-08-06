#!/usr/bin/env python

##
##  Copyright 2012-2014 SRI International
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

import codecs
import re

# Copy an ePrime (Stroop) file while sanitizing it, i.e., removing personally-identifiable information
def copy_sanitize( eprime_in, eprime_out ):
    # List of "banned" ePrime log file keys - these are removed from the file while copying
    banned_keys = [ 'name', 'age', 'sessiondate', 'sessiontimeutc', 'subject', 'session', 'clock.information' ]

    try:
        infile = codecs.open( eprime_in, 'Ur', 'utf-16' )
        try:
            outfile = open( eprime_out, 'w' )

            for line in infile.readlines():
                match = re.match( '^\s*([^:]+):.*$', line )
                if not (match and (match.group(1).lower() in banned_keys)):
                    outfile.write( line )
            
            outfile.close()
        except:
            print "ERROR: failed to open output file",eprime_out

        infile.close()

    except:
        print "ERROR: failed to open input file",eprime_in


# Command line interface, if run directly
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser( description="Copy an ePrime log file and sanitize (remove) potentially confidential information", formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser.add_argument( "infile", help="Input file path")
    parser.add_argument( "outfile", help="Output file path")
    args = parser.parse_args()

    copy_sanitize( args.infile, args.outfile )
