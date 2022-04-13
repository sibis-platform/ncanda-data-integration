#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

from builtins import str
import pandas as pd
import sibispy
from sibispy import sibislogger as slog
import os

def upload_findings_to_xnat(
    sibis_session: sibispy.Session,
    qc_csv_file: str,
    sendEmailFlag: bool
) -> int:
    if not os.path.exists(qc_csv_file):
        raise IOError("Please ensure {} exists!".format(qc_csv_file))

    ##############
    # INPUT DATA
    try: 
       fData=pd.read_csv(qc_csv_file)
    except Exception as err_msg :
       raise IOError("Reading of File {} failed with the following error message: {}".format(qc_csv_file,str(err_msg)))
 
    questionable_scans="" 
    uploaded_scan_count = 0
    for index,row in fData.iterrows():

        exp=sibis_session.xnat_get_experiment(row['xnat_experiment_id'])
        if exp is None:
            import hashlib
            slog.info("upload_findings_to_xnat-{}-{}".format(row['xnat_experiment_id'],hashlib.sha1('upload_findings_to_xnat_{xnat_experiment_id}'.format(**row).encode()).hexdigest()[0:6]),
                'Experiment "{xnat_experiment_id}" from CSV file "{csv_file}" does not exist in XNAT.'.format(csv_file=qc_csv_file, **row),
                src='upload_findings_to_xnat')
            continue
        scan=exp.scans.get(str(row['scan_id']))
        if scan is None:
            import hashlib
            slog.info("upload_findings_to_xnat-{}-{}".format(row['xnat_experiment_id'],hashlib.sha1('upload_findings_to_xnat_{xnat_experiment_id}'.format(**row).encode()).hexdigest()[0:6]),
                'Scan {scan_id} for Experiment "{xnat_experiment_id}" from CSV file "{csv_file}" does not exist in XNAT.'.format(csv_file=qc_csv_file, **row),
                src='upload_findings_to_xnat')
            continue

        try:
            # quality - only change if the scan quality isn't determined yet
            if scan.get('quality') in ['unusable', 'usable', 'usable-extra']:
                pass  # prevent the elifs that set scan quality from executing
            elif row['decision']==1:
                scan.set('quality', 'usable')
                uploaded_scan_count += 1
            elif row['decision'] == 2:
                scan.set('quality', 'usable-extra')
                uploaded_scan_count += 1
            elif row['decision']==0:
                scan.set('quality', 'questionable')
                uploaded_scan_count += 1
                questionable_scans +=  row['xnat_experiment_id'] + " " + str(row['scan_id']);
                if isinstance(row['scan_note'],str) and len(row['scan_note'])>0:
                        questionable_scans +=  " " + row['scan_note']

                questionable_scans +=  " " + str(os.path.join(row['nifti_folder'],str(row['scan_id']) + "_" + str(row['scan_type']), "*.gz")) +  "<BR>" 
            else:
                scan.set('quality','unknown')

            # comment - always upload
            if isinstance(row['scan_note'],str) and len(row['scan_note'])>0:
                scan.set('note',row['scan_note'])

        except Exception as e:
            import hashlib, sys, traceback
            slog.info(hashlib.sha1('upload_findings_to_xnat_{}'.format(row['xnat_experiment_id'])).hexdigest()[0:6], 
                      'Problem processing findings for upload, exp: {}'.format(row['xnat_experiment_id']),
                      error_msg=e.message,
                      error_detail=traceback.format_exception(sys.exec_info()))
            continue 

    # send email to qc manager
    if sendEmailFlag and len(questionable_scans) :
        from sibispy import sibis_email 
        email = sibis_email.xnat_email(sibis_session)

        email.send('%s XNAT - Questionable Scans' % sibis_session.get_project_name(),
                   email._admin_email,
                   [email._admin_email],
                   str(questionable_scans),
                   False)    

    return uploaded_scan_count

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


