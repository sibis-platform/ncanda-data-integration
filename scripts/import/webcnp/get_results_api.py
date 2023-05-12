#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import sys
import json
import sibispy
from sibispy import sibislogger as slog
from sibispy import config_file_parser as cfg_parser
import requests
import pandas as pd
from typing import List
import argparse
from datetime import date
from dateutil.relativedelta import relativedelta

def get_start_date(args):
    start_date = None
    
    if args.on_date:
        pass
    elif args.from_date:
        # retrieve data from date til today
        start_date = args.from_date
        pass
    elif args.last_month:
        # retrieve data from just last month
        start_date = (date.today() + relativedelta(months=-1)).isoformat()
    elif args.last_3_months:
        # retirve data from last three months (default)
        start_date = (date.today() + relativedelta(months=-3)).isoformat()
    elif args.last_year:
        # retrieve data from the last year
        start_date = (date.today() + relativedelta(years=-1)).isoformat()
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
    df = whole_df[whole_df["test_sessions_v_dotest"] >= start_date]
    
    # drop unneeded columns
    df = df.drop('record_id', axis=1)
    
    return df
    
def get_penn_data(args):

    cfg = cfg_parser.config_file_parser()
    cfg.configure(args.config)
    
    try:
        token = cfg.get_category('penncnp')['token']
    except:
        slog.info("get_results_api","Error: sibis-general-config file was not found")
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
    
    import pdb; pdb.set_trace()
    # Check if config file exists - read user name and password if it does, bail otherwise
    sibis_session = sibispy.Session()
    if not sibis_session.configure() :
        slog.info("get_results_api","Error: session configure file was not found")
        sys.exit()

    try:
        data = get_penn_data(args)
        data.to_csv(args.out_dir, index=False)
    except:
        slog.info("get_results_api","Error: could not get penn data")
        sys.exit()
        
    slog.takeTimer1("script_time") 
    
if __name__ == "__main__":
    # TODO: add arguments
    """
    arguments needed:
    - verbose
    - post errors to github ?
    - config file location
    - output file location
    - date range
    """
    main()