#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import pandas as pd
import sibispy
from sibispy import sibislogger as slog
import os

def upload_findings_to_xnat(sibis_session,qc_csv_file, sendEmailFlag): 
    if not os.path.exists(qc_csv_file):
        raise IOError("Please ensure {} exists!".format(qc_csv_file))

    ##############
    # INPUT DATA
    try: 
       fData=pd.read_csv(qc_csv_file)
    except Exception as err_msg :
       raise IOError("Reading of File {} failed with the following error message: {}".format(qc_csv_file,str(err_msg)))
 
    questionable_scans="" 
    for index,row in fData.iterrows():

        exp=sibis_session.xnat_get_experiment(row['xnat_experiment_id'])
        scan=exp.scans[str(row['scan_id'])]

        # quality
        if row['decision']==1:
                scan.set('quality','usable')
        elif row['decision']==0:
                scan.set('quality','questionable')
                questionable_scans +=  row['xnat_experiment_id'] + " " + str(row['scan_id']);
                if isinstance(row['scan_note'],str) and len(row['scan_note'])>0:
                        questionable_scans +=  " " + row['scan_note']

                questionable_scans +=  " " + str(os.path.join(row['nifti_folder'],str(row['scan_id']) + "_" + str(row['scan_type']), "*.gz")) +  "<BR>" 
        else:
                scan.set('quality','unknown')

        # comment
        if isinstance(row['scan_note'],str) and len(row['scan_note'])>0:
		scan.set('note',row['scan_note'])

    # send email to qc manager
    if sendEmailFlag and len(questionable_scans) :
        from sibispy import sibis_email 
        email = sibis_email.xnat_email(sibis_session)

        email.send('%s XNAT - Questionable Scans' % sibis_session.get_project_name(),
                   email._admin_email,
                   email._admin_email,
                   str(questionable_scans),
                   False)    

#============================================================
# Main
#============================================================
if __name__ == "__main__": 
    import argparse
    # example input /fs/ncanda-share/log/check_new_sessions/scans_to_review.csv
    parser = argparse.ArgumentParser(description="Uploads qc results to XNAT" )
    parser.add_argument("qc_csv_file",help="csv file with qc results",action="store")
    args = parser.parse_args()

    ###########
    # SESSION
    slog.init_log(False, False,'upload_visual_qc', 'upload_visual_qc','/tmp')
    session = sibispy.Session()
    session.configure()
    server = session.connect_server('xnat', True)

    upload_findings_to_xnat(session,args.qc_csv_file, True)


