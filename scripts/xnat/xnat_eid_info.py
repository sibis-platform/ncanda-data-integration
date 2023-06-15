#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##  returns important information associated with the experiment of eid  
##

from builtins import str
import pandas as pd
import sibispy
from sibispy import sibislogger as slog
import sys

def init_session() :
    slog.init_log(False, False,'xnat_eid_info', 'xnat_eid_info')
    session = sibispy.Session()
    session.configure()
    session.connect_server('xnat', True)
    return session

def eid_info(sibis_session,eid,verbose=False) :
    exp=sibis_session.xnat_get_experiment(eid)
    if exp is None:
        if verbose :
            print("ERROR:No record found for",eid)
        print(eid+",,,")    
        return 1
    print(','.join([eid,exp.label,exp.subject_id,exp.project]))
    return 0

#============================================================
# Main
#============================================================
if __name__ == "__main__": 
    import argparse
    # example NCANDA_E12152
    parser = argparse.ArgumentParser(description="Lookup info related to experiment with eid" )
    parser.add_argument("eid",help="eid",action="store")
    parser.add_argument("-v", "--verbose", help="Verbose operation", action="store_true")
    args = parser.parse_args()

    sibis_session=init_session()
    sys.exit(eid_info(sibis_session,args.eid, args.verbose))


