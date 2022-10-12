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
import miqa_file_generation

def upload_findings_to_xnat(
        sibis_session: sibispy.Session,
        qc_csv_file: str,
        sendEmailFlag: bool,
        verbose: bool
) -> int:
    
    if verbose:
        print(f"Uploading decisions from {qc_csv_file} to xnat")
            
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
                      f'Experiment "{xnat_experiment_id}" from CSV file "{csv_file}" does not exist in XNAT.',
                      src='upload_findings_to_xnat')
            continue
        scan=exp.scans.get(str(row['scan_id']))
        if scan is None:
            import hashlib
            slog.info("upload_findings_to_xnat-{}-{}".format(row['xnat_experiment_id'],hashlib.sha1('upload_findings_to_xnat_{xnat_experiment_id}'.format(**row).encode()).hexdigest()[0:6]),
                      f'Scan {scan_id} for Experiment "{xnat_experiment_id}" from CSV file "{csv_file}" does not exist in XNAT.',
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
            scan_note=row['scan_note']
            if isinstance(scan_note,str) :
                scan_note_len=len(scan_note)
                if  scan_note_len :
                    if scan_note_len > 254 :
                        uploaded_note= scan_note[:254]

                        import hashlib
                        eLabel=row['xnat_experiment_id'] + "-" + str(row['scan_id']) + "-" + hashlib.sha1(scan_note.encode()).hexdigest()[0:6]
                        slog.info(eLabel,
                                  'Could not upload complete scan notes',
                                  experiment= row['xnat_experiment_id'] ,
                                  scan_id= row['scan_id'],
                                  original_scan_note=scan_note,
                                  uploaded_scan_note=uploaded_note,
                                  info="XNAT  resticts scan notes to less than 255 characters. If uploaded_scan_note misses important details,  edit scan note in xnat directly so that you stay under the character count.  Close issue afterwards or when nothing needs to be edit")

                    else :
                        uploaded_note=scan_note
                   
                scan.set('note',uploaded_note)

        except Exception as e:
                import hashlib, sys, traceback
                sys_info=sys.exc_info()
                eLabel=row['xnat_experiment_id']  + "-" + str(row['scan_id']) + "-" + hashlib.sha1(str(e).encode()).hexdigest()[0:6]
                slog.info(eLabel,
                          'Could not upload information for exp: {}'.format(row['xnat_experiment_id']),
                          experiment= row['xnat_experiment_id'] ,
                          scan= str(row['scan_id']),
                          error_msg=e,
                          error_detail=traceback.format_exception(sys_info[0],sys_info[1],sys_info[2]))
                                        
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



def upload_2nd_tier_to_xnat(
        sibis_session: sibispy.Session,
        qc_file: str,
        verbose: bool
) -> int:

    if verbose:
        print(f"Uploading decisions from {qc_file} to xnat")

    qc_dict=miqa_file_generation.read_miqa_import_file(qc_file,"", verbose,format=miqa_file_generation.MIQAFileFormat.JSON)
        
    questionable_scans="" 
    uploaded_scan_count = 0
    
    qc_projects=qc_dict['projects']
    for SITE,site_dict in qc_projects.items() :
        exps_dict = site_dict["experiments"]
        for eID,exp_dict in exps_dict.items() :
            exp=sibis_session.xnat_get_experiment(eID)
            if exp is None:
                import hashlib
                slog.info("upload_findings_to_xnat-{}-{}".format(eID,hashlib.sha1('upload_findings_to_xnat_{eID}'.encode()).hexdigest()[0:6]),
                          f'Experiment "{eID}" from json file "{qc_file}" does not exist in XNAT.',
                          src='upload_upload_2nd_tier_to_xnat')
                continue
            
            # overal experiment notes are always uploaded
            exp_note=exp_dict['notes']
            if isinstance(exp_note,str) :
                note_len=len(exp_note)
                if  note_len :
                    print("Uploaded:", eID,exp_note)  
                    exp.set("note",exp_note)
 
            for scan_id,scan_dict in exp_dict['scans'].items() :
                
                sID= scan_id.split('_')[0]
                scan=exp.scans.get(sID)
                if scan is None:
                    import hashlib
                    slog.info("upload_findings_to_xnat-{}-{}".format(eID,hashlib.sha1('upload_findings_to_xnat_{eID}_{sID}'.encode()).hexdigest()[0:6]),
                              f'Could not find scan "{sID}" for Experiment "{eID}" from json file "{qc_file}" .',
                              NCANDA_SID=scan_dict['subject_id'],
                              SESSION_ID=scan_dict['session_id'],
                              XNAT_LINK=scan_dict['scan_link'],
                              src='upload_upload_2nd_tier_to_xnat')
                    continue

                # Upload decision
                scan_qc=scan_dict['last_decision']
                scan_decision=scan_qc['decision']

                try:
                    # quality - only change if the scan quality isn't determined yet
                    if scan.get('quality') in ['unusable', 'usable', 'usable-extra']:
                        pass  # prevent the elifs that set scan quality from executing
                    elif scan_decision =='U':
                        uploaded_scan_count += 1
                        scan.set('quality', 'usable')
                    elif scan_decision == 'UE':
                        uploaded_scan_count += 1
                        scan.set('quality', 'usable-extra')
                    elif scan_decision == 'UN':
                        uploaded_scan_count += 1
                        scan.set('quality', 'unusable')
                    elif scan_decision =='Q?':
                        uploaded_scan_count += 1
                        scan.set('quality', 'questionable')
                    else:
                        # scan.set('quality','unknown')
                        import hashlib
                        slog.info("upload_findings_to_xnat-{}-{}".format(eID,hashlib.sha1('upload_findings_to_xnat_{eID}_{sID}'.encode()).hexdigest()[0:6]),
                                  f'Decision {scan_decision } for Scan {sID} and Experiment "{eID}" from json file "{qc_file}" does not match XNAT setings.',
                                  NCANDA_SID=scan_dict['subject_id'],
                                  SESSION_ID=scan_dict['session_id'],
                                  XNAT_LINK=scan_dict['scan_link'],
                                  src='upload_upload_2nd_tier_to_xnat')
                        continue
                    
                except Exception as e:
                    import hashlib, sys, traceback
                    sys_info=sys.exc_info()
                    eLabel=eID  + "-" + sID + "-" + hashlib.sha1(str(e).encode()).hexdigest()[0:6]
                    slog.info(eLabel,
                              'Could not upload information for exp: {}'.format(eID),
                              experiment= eID ,
                              scan= sID,
                              NCANDA_SID=scan_dict['subject_id'],
                              SESSION_ID=scan_dict['session_id'],
                              XNAT_LINK=scan_dict['scan_link'],
                              error_msg=e,
                              error_detail=traceback.format_exception(sys_info[0],sys_info[1],sys_info[2]))
                    
                    continue 
                     
        # comment - always upload
        scan_note=scan_qc['note']
        # print(eID,sID, scan_id, scan_decision , scan_note)
        if isinstance(scan_note,str) :
                scan_note_len=len(scan_note)
                if  scan_note_len :
                    if scan_note_len > 254 :
                        uploaded_note= scan_note[:254]

                        import hashlib
                        eLabel=eID + "-" + sID + "-" + hashlib.sha1(scan_note.encode()).hexdigest()[0:6]
                        slog.info(eLabel,
                                  'Could not upload complete scan notes',
                                  experiment= eID ,
                                  scan_id= sID,
                                  original_scan_note=scan_note,
                                  uploaded_scan_note=uploaded_note,
                                  NCANDA_SID=scan_dict['subject_id'],
                                  SESSION_ID=scan_dict['session_id'],
                                  XNAT_LINK=scan_dict['scan_link'],
                                  info="XNAT  resticts scan notes to less than 255 characters. If uploaded_scan_note misses important details,  edit scan note in xnat directly so that you stay under the character count.  Close issue afterwards or when nothing needs to be edit")
                    else :
                        uploaded_note=scan_note
                        
                print("Uploaded",eID,sID,uploaded_note)  
                scan.set('note',uploaded_note)

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


