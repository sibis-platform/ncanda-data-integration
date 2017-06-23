#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
==================
REDCap Form Locker
==================

Provides a CLI to lock and unlock REDCap forms.

Example Usage:

python redcap_form_locker.py --project ncanda_subject_visit_log
                             --arm Standard Protocol
                             --event Baseline visit
                             --form demographics
                             --username nicholsn (need locking permissions)
                             --lock or --unlock
"""

import os
import sys
import datetime

import pandas as pd
from pandas.io.sql import execute

import sibispy
from sibispy import sibislogger as slog



def get_project_id(project_name, engine):
    """
    Get the project ID from a project_name

    :param project_name: str
    :param engine: sqlalchemy.Engine
    :return: int
    """
    projects = pd.read_sql_table('redcap_projects', engine)
    project_id = projects[projects.project_name == project_name].project_id
    return int(project_id)


def get_arm_id(arm_name, project_id, engine):
    """
    Get an arm_id using the arm name and project_id

    :param arm_name: str
    :param project_id: int
    :param engine: `sqlalchemy.Engine`
    :return: int
    """
    arms = pd.read_sql_table('redcap_events_arms', engine)
    arm_id = arms[(arms.arm_name == arm_name) & (arms.project_id == project_id)].arm_id
    return int(arm_id)


def get_event_id(event_descrip, arm_id, engine):
    """
    Get an event_id using the event description and arm_id

    :param event_descrip: str
    :param arm_id: int
    :param engine: `sqlalchemy.Engine`
    :return: int
    """
    events = pd.read_sql_table('redcap_events_metadata', engine)
    event_id = events[(events.descrip == event_descrip) & (events.arm_id == arm_id)].event_id
    return int(event_id)


def get_locked_records(project_name, arm_name, event_descrip, engine, site_id=None):
    """
    Get a dataframe of locked forms for a specific event

    :param project_name: str
    :param arm_name: str
    :param event_descrip: str
    :param engine: `sqlalchemy.Engine`
    :return: pandas.DataFrame`
    """
    project_id = get_project_id(project_name, engine)
    arm_id = get_arm_id(arm_name, project_id, engine)
    event_id = get_event_id(event_descrip, arm_id, engine)
    locked_records = pd.read_sql_table('redcap_locking_data', engine)
    locked_forms = locked_records[(locked_records.project_id == project_id) &
                                  (locked_records.event_id == event_id)]
    if site_id:
        locked_forms = locked_forms[locked_forms.record == site_id]
    return locked_forms


def get_project_records(project_name, arm_name, event_descrip, engine, subject_id = None ):
    """
    Get a dataframe of records for a specific event

    :param project_name: str
    :param arm_name: str
    :param event_descrip: str
    :param engine: `sqlalchemy.Engine`
    :return: `pandas.DataFrame`
    """
    project_id = get_project_id(project_name, engine)
    arm_id = get_arm_id(arm_name, project_id, engine)
    event_id = get_event_id(event_descrip, arm_id, engine)
    sql = "SELECT DISTINCT record " \
          "FROM redcap.redcap_data AS rd " \
          "WHERE rd.project_id = {0} " \
          "AND rd.event_id = {1}".format(project_id, event_id)
    if subject_id :
        sql +=  " AND rd.record = '{0}';".format(subject_id)
    else :
        sql +=";"
        
    records = pd.read_sql(sql, engine)
    
    return records


def unlock_form(project_name, arm_name, event_descrip, form_name, engine, subject_id = None):
    """
    Unlock a given form be removing records from table

    :param project_name: str
    :param arm_name: str
    :param event_descrip: str
    :param form_name: str
    :param engine: `sqlalchemy.Engine`
    :param subject_id: str
    :return: None
    """
    # get ids needed for unlocking
    project_id = get_project_id(project_name, engine)
    arm_id = get_arm_id(arm_name, project_id, engine)
    event_id = get_event_id(event_descrip, arm_id, engine)
    # get a list of all the locked records and filter for records to remove
    locked_records = pd.read_sql_table('redcap_locking_data', engine)
    locked_forms = locked_records[(locked_records.project_id == project_id) &
                                  (locked_records.event_id == event_id) &
                                  (locked_records.form_name == form_name)]
    if subject_id : 
        locked_forms = locked_forms[(locked_forms.record == subject_id)]

    # generate the list of ids to drop and remove from db table
    global locked_list
    locked_list = ', '.join([str(i) for i in locked_forms.ld_id.values.tolist()])
    if locked_list:
        sql = 'DELETE FROM redcap_locking_data ' \
              'WHERE redcap_locking_data.ld_id IN ({0});'.format(locked_list)
        execute(sql, engine)
        return True
    else :
        return False

def lock_form(project_name, arm_name, event_descrip, form_name, username, outfile, engine, subject_id = None):
    """
    Lock all records for a given form for a project and event

    :param project_name: str
    :param arm: str
    :param event_descrip: str
    :param form_name: str
    :param username: str (must have locking permissions)
    :param engine: `sqlalchemy.Engine`
    :return:
    """
    # get the ids needed to lock the forms
    project_id = get_project_id(project_name, engine)
    arm_id = get_arm_id(arm_name, project_id, engine)
    event_id = get_event_id(event_descrip, arm_id, engine)
    # get the pd.Series needed to construct a dataframe
    global project_records
    project_records = get_project_records(project_name, arm_name,
                                          event_descrip, engine, subject_id)
        
    project_id_series = [project_id] * len(project_records)
    event_id_series = [event_id] * len(project_records)
    form_name_series = [form_name] * len(project_records)
    username_series = [username] * len(project_records)
    locking_records = dict(project_id=project_id_series,
                           record=project_records.record.tolist(),
                           event_id=event_id_series,
                           form_name=form_name_series,
                           username=username_series,
                           timestamp=datetime.datetime.now())

    dataframe = pd.DataFrame(data=locking_records)
    # first make sure all these forms are unlocked before locking
    unlock_form(project_name, arm_name, event_descrip, form_name, engine, subject_id)
    # lock all the records for this form by appending entries to locking table
    # Kilian: Problem this table is created regardless if the form really exists in redcap or not
    dataframe.to_sql('redcap_locking_data', engine, if_exists='append', index=False)
    dataframe.record.to_csv(outfile, index=False)


def report_locked_forms(site_id, xnat_id, forms, project_name,
                        arm_name, event_descrip, engine):
    """
    Generate a report for a single subject reporting all of the forms that
    are locked in the database using the timestamp the record was locked

    This is called in export_redcap_to_pipeline.export()

    :param site_id: str (e.g., X-12345-G-6)
    :param xnat_id: str (e.g., NCANDA_S12345)
    :param forms: list
    :param project_name: str (e.g., ncanda_subject_visit_log)
    :param arm_name: str (e.g., Standard)
    :param event_descrip: str (e.g., Baseline)
    :param engine: `sqlalchemy.Engine`
    :return: `pandas.DataFrame`
    """

    columns = ['subject', 'arm', 'visit'] + list(forms)
    data = dict(subject=xnat_id, arm=arm_name.lower(), visit=event_descrip.lower())
    dataframe = pd.DataFrame(data=data, index=[0], columns=columns)
    locked_forms = get_locked_records(project_name, arm_name, event_descrip, engine, site_id=site_id)
    for _, row in locked_forms.iterrows():
        form_name = row.get('form_name')
        timestamp = row.get('timestamp')
        dataframe.set_value(0, form_name, timestamp)
    return dataframe


def main(args=None):
    if not args:
        return 
    
    slog.startTimer1()
    session = sibispy.Session()
    if not session.configure() :
        if args.verbose:
            print "Error: session configure file was not found"

        sys.exit(1)

    engine = session.connect_server('redcap_mysql_db', True)
    if not engine :
        if args.verbose:
            print "Error: Could not connect to REDCap mysql db"

        sys.exit(1)

    if args.verbose:
        print "Connected to REDCap using: {0}".format(engine)

    if args.unlock and args.lock:
        raise Exception("Only specify --lock or --unlock, not both!")

    if args.lock:
        if args.verbose:
            print "Attempting to lock form: {0}".format(args.form)
        lock_form(args.project, args.arm, args.event, args.form,
                  args.username, args.outfile, engine , subject_id = args.subject_id)
        slog.takeTimer1("script_time","{'records': " + str(len(project_records)) + "}")
        if args.verbose:
            print "The {0} form has been locked".format(args.form)
            print "Record of locked files: {0}".format(args.outfile)

    elif args.unlock:
        if args.verbose:
            print "Attempting to unlock form: {0}".format(args.form)

        if not unlock_form(args.project, args.arm, args.event, args.form, engine, subject_id = args.subject_id):
            print "Warning: Nothing to unlock ! Form '{0}' might not exist".format(args.form)
        elif args.verbose:
            print "The {0} form has been unlocked".format(args.form)

    elif args.report:
        if args.verbose:
            print "Attempting to create a report for form {0} and subject_id {1} ".format(args.form,args.subject_id)
        print report_locked_forms(args.subject_id, args.subject_id, [ args.form ], args.project, args.arm, args.event, engine)

    else :
        raise Exception("Please specify --lock, --unlock, or --report!")
            
    if args.verbose:
        print "Done!"

    slog.takeTimer1("script_time")

if __name__ == "__main__":
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="redcap_form_locker.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument("--project", dest="project", required=True,
                        help="Project Name in lowercase_underscore.")
    parser.add_argument("-a", "--arm", dest="arm", required=True,
                        choices=['Standard Protocol'],
                        help="Arm Name as appears in UI")
    parser.add_argument("-e", "--event", dest="event", required=True,
                        choices=['Baseline visit', '1y visit', '2y visit'],
                        help="Event Name in as appears in UI")
    parser.add_argument("-f", "--form", dest="form", required=True,
                        help="Form Name in lowercase_underscore")
    parser.add_argument("-o", "--outfile", dest="outfile",
                        default=os.path.join('/tmp', 'locked_records.csv'),
                        help="Path to write locked records file. {0}".format(default))
    parser.add_argument("-s", "--subject_id", default=None, help="REDCap subject ID")
    parser.add_argument("-u", "--username", dest="username", required=True,
                        help="User Name with locking permissions")
    parser.add_argument("--lock", dest="lock", action="store_true",
                        help="Lock form")
    parser.add_argument("--unlock", dest="unlock", action="store_true",
                        help="Lock forms")
    parser.add_argument("--report", dest="report", action="store_true",
                        help="Generate a report for subject")

    parser.add_argument("-v", "--verbose", dest="verbose",
                        help="Turn on verbose", action='store_true')
    parser.add_argument("-p", "--post-to-github", help="Post all issues to GitHub instead of std out.", action="store_true")
    parser.add_argument("-t","--time-log-dir", help="If set then time logs are written to that directory", action="store", default=None)

    args = parser.parse_args()

    slog.init_log(args.verbose, args.post_to_github,'NCANDA REDCap', 'redcap_form_locker', args.time_log_dir)

    sys.exit(main(args=args))
