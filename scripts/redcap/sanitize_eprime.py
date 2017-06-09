#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
import codecs
import re
from sibispy import sibislogger as slog

# Copy an ePrime (Stroop) file while sanitizing it, i.e., removing personally-identifiable information
def copy_sanitize(redcap_visit_id,eprime_in, eprime_out ):
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
            slog.info(redcap_visit_id, "ERROR: failed to open output file " + str(eprime_out))

        infile.close()

    except:
        slog.info(redcap_visit_id, "ERROR: failed to open input file " + str(eprime_in))



# Command line interface, if run directly
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser( description="Copy an ePrime log file and sanitize (remove) potentially confidential information", formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser.add_argument( "infile", help="Input file path")
    parser.add_argument( "outfile", help="Output file path")
    args = parser.parse_args()

    copy_sanitize('sanatize_eprime',args.infile, args.outfile )
