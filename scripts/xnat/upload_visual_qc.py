#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import argparse
import pandas as pd
import sibispy
from sibispy import sibislogger as slog

# example input /fs/ncanda-share/log/check_new_sessions/scans_to_review.csv
parser = argparse.ArgumentParser(description="Uploads qc results to XNAT" )
parser.add_argument("qc_csv_file",help="csv file with qc results",action="store")
args = parser.parse_args()

##############
# INPUT DATA
f=pd.read_csv(args.qc_csv_file)


###########
# SESSION
slog.init_log(False, False,'upload_visual_qc', 'upload_visual_qc','/tmp')
session = sibispy.Session()
session.configure()
server = session.connect_server('xnat', True)
for index,row in f.iterrows():
        exp=session.xnat_get_experiment(row['xnat_experiment_id'])
        sc=exp.scan(str(row['scan_id'])).attrs

        # quality
        if row['decision']==1:
                sc.set('quality','usable')
        elif row['decision']==0:
                sc.set('quality','questionable')
        else:
                sc.set('quality','unknown')

#        elif row['decision']==-1:
#                sc.set('quality','unusable')


        # comment
        if len(row['scan_note'])>0:
		sc.set('note',row['scan_note'])

