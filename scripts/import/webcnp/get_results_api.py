#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import sys
import os
import json
import subprocess
import sibispy
from sibispy import sibislogger as slog
from sibispy import config_file_parser as cfg_parser
import requests
import pandas as pd
from typing import List
import argparse
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


def set_file_name(args):
    """Set file name for csv in out_dir"""
    today = datetime.today()
    dt_string = today.strftime("%Y%m%d_%H%M%S")
    file_name = "/" + dt_string + "_cnp_api_results.csv"
    return file_name
    
def get_start_date(args):
    """Get the start date for the data to be selected"""
    start_date = None
    
    if args.on_date:
        start_date = args.on_date
    elif args.from_date:
        # retrieve data from date til today
        start_date = args.from_date
    elif args.last_month:
        # retrieve data from just last month
        start_date = (date.today() + relativedelta(months=-1)).isoformat()
    elif args.last_3_months:
        # retirve data from last three months (default)
        start_date = (date.today() + relativedelta(months=-3)).isoformat()
    elif args.last_year:
        # retrieve data from the last year
        start_date = (date.today() + relativedelta(years=-1)).isoformat()
    else:
        # if no argument is passed, assyume it is the last 3 months
        start_date = (date.today() + relativedelta(months=-3)).isoformat()
    return start_date

def get_desired_data(args, whole_df):
    """
    From the whole dataset, select the values that are desired within the 
    given date range.
    Note: Dates must be YYYY-MM-DD
    """
    start_date = get_start_date(args)
    if not start_date:
        slog.info("get_results_api","Error: could not get valid start date")
        sys.exit()
    
    # select the values from the dataframe with date values greater than start
    # date column is test_sessions_v_dotest
    if args.on_date:
        df = whole_df[whole_df["test_sessions_v_dotest"] == start_date]
    else:
        df = whole_df[whole_df["test_sessions_v_dotest"] >= start_date]
    
    # drop unneeded columns
    df = df[df.columns.drop(list(df.filter(regex='complete$')))]
    df = df.drop('record_id', axis=1)
    
    # convert non test-session cols to match data dict
    orig_col_list = df.columns
    upper_col_list = []
    
    for val in orig_col_list:
        if not val.startswith('test_sessions'):
            new_val =  val.upper()
            upper_col_list.append(new_val)
        else:
            upper_col_list.append(val)            
    
    rename_map = dict(zip(orig_col_list, upper_col_list))
    df.rename(rename_map, axis=1, inplace=True)
    
    # add in the spvrt status column as complete
    df['pvrt_status'] = 'C1'
    
    return df
    
def get_penn_data(args):
    """Submit the api request to PennCNP and return the data"""
    cfg = cfg_parser.config_file_parser()
    cfg.configure(args.config)
    
    try:
        token = cfg.get_category('penncnp')['token']
    except:
        slog.info("get_results_api","Error: sibis-general-config file was not found or token was not found")
        sys.exit()
    
    # get full data dump
    data = {
        'token': token,
        'content': 'record',
        'action': 'export',
        'format': 'json',
        'type': 'flat',
        'csvDelimiter': '',
        'rawOrLabel': 'raw',
        'rawOrLabelHeaders': 'raw',
        'exportCheckboxLabel': 'false',
        'exportSurveyFields': 'false',
        'exportDataAccessGroups': 'false',
        'returnFormat': 'json'
    }
    r = requests.post('https://redcap.med.upenn.edu/api/',data=data)
    data = json.loads(r.text)
    df = pd.DataFrame(data)
    
    result = get_desired_data(args, df)

    return result

def parse_args(input_args: List[str] = None):
    parser = argparse.ArgumentParser( description="Retrieve CSV spreadsheet from WebCNP database at U Penn" )
    parser.add_argument( "-v", "--verbose", help="Verbose operation", action="store_true" )
    parser.add_argument("--config", help="Path to the sibis-general-config.yml file.",
                        action="store")
    
    period = parser.add_mutually_exclusive_group()
    period.add_argument( "--from-date", help="Retrieve only records from the specific date onwards. Give date as 'YYYY-MM-DD'.", action="store" )
    period.add_argument( "--on-date", help="Retrieve only records from the specific date. Give date as 'YYYY-MM-DD'.", action="store")
    period.add_argument( "--last-month", help="Retrieve only records of the last month.", action="store_true" )
    period.add_argument( "--last-3-months", help="Retrieve only records of the last 3 months.", action="store_true" )
    period.add_argument( "--last-year", help="Retrieve only records of the last year.", action="store_true" )

    parser.add_argument("-p", "--post-to-github", help="Post all issues to GitHub instead of std out.", action="store_true")
    
    parser.add_argument("-t","--time-log-dir",
                        help="If set then time logs are written to that directory",
                        action="store",
                        default=None)
    parser.add_argument( "out_dir", help="Directory for output files" )

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    
    slog.init_log(args.verbose, args.post_to_github,'NCANDA Import', 'get_results_api', args.time_log_dir)
    slog.startTimer1()

    # Check if config file exists - read user name and password if it does, bail otherwise
    sibis_session = sibispy.Session()
    if not sibis_session.configure() :
        slog.info("get_results_api","Error: session configure file was not found")
        sys.exit()

    try:
        # get data from penn api call and format correctly
        data = get_penn_data(args)
        
        # create out_dir if it does not exist
        if not os.path.exists(args.out_dir):
            os.mkdir(args.out_dir)
            subprocess.call(['chmod', '-R', 'a+wr', args.out_dir])

        file_name = set_file_name(args)
        
        # set full path for file to write
        out_file_path = args.out_dir + file_name

        # write data to csv in out_dir
        data.to_csv(out_file_path, index=False)
        os.chmod(out_file_path, 0o777)
        
    except Exception as e:
        slog.info("get_results_api", 
                "Could not get data from Penn api",
                info="There was an error encountered when trying to get data from PennCNP api call.",
                err_msg=str(e),
            )
        sys.exit()
        
    slog.takeTimer1("script_time") 
    
if __name__ == "__main__":
    main()