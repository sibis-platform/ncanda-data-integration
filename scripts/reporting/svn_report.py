#!/usr/bin/env python3

'''
This file creates a .csv file containing the name of each laptop and its last changed date
'''
import argparse
import csv
from datetime import datetime, timezone
import os
import svn.local
import pandas as pd
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

'''
Constants -- paths for reports, default save names, SLA, columns, and sites
TO-DO: Change SLA_DAYS to a parser arg?
'''
REPORTS_DIR = '/fs/storage/laptops/ncanda'
DEFAULT_CSV = '/fs/ncanda-share/log/status_reports/sla_files/'
SLA_DAYS = 30
DATA_COLUMNS = ['laptop', 'date_updated', 'time_diff', 'sla', 'sla_percentage']
SITES = ['duke', 'sri', 'ohsu', 'upmc', 'ucsd']
CONFIG_FILE = 'svn_report_config.yml'

def parse_args(arg_input=None):
    '''
    Set up parser arguments
    '''
    parser = argparse.ArgumentParser(
        description="Create a CSV file with all laptops and dates they were last modified")
    parser.add_argument(
        "--file",
        help="Path of file name to save as",
        action="store",
        default=DEFAULT_CSV)
    
    return parser.parse_args(arg_input)

def load_default_sla(path=None):
    '''
    Loads default SLA from YAML file
    '''
    with open(path) as f:
        data = load(f, Loader=Loader)
        return data['three'], data['dead']

def create_dataframe(three_sla, dead_sla):
    '''
    Writes the names of each laptop and the date they were updated to a .csv file
    '''
    # Grab all directories and set up SVN client
    directories = os.listdir(REPORTS_DIR)
    r = svn.local.LocalClient(REPORTS_DIR)
    df = pd.DataFrame(columns=DATA_COLUMNS)
    
    # Calculate time difference and appends to csv file
    for directory in directories:
        if (directory != ".svn"):
            # Get commit date, time difference from today, and percentage of SLA
            info = r.info(directory)
            mod_time = info['commit/date']
            time_diff = datetime.now(timezone.utc) - mod_time
            laptop_sla = SLA_DAYS

            # Parsing through default SLA cases
            if directory in three_sla:
                laptop_sla = 3
            elif directory in dead_sla:
                laptop_sla = 3000
            sla_percentage = time_diff.total_seconds() / (laptop_sla * 24 * 60 * 60)
                
            new_row = {
                'laptop': directory,
                'date_updated': mod_time,
                'time_diff': time_diff,
                'sla': laptop_sla,
                'sla_percentage': sla_percentage
                }
            df = df.append(new_row, ignore_index=True)

    # Sort by descending SLA percentage
    df = df.sort_values(by=['sla_percentage'], ascending=False)
    return df

def write_to_csv(df, path=None):
    '''
    Save data into a dataframe and save for each individual site
    '''
    df.to_csv(path + 'reports.csv', index=False)
    for site in SITES:
        site_df = df.loc[df['laptop'].str.contains(site, case=False)]
        site_df.to_csv(path + site + '.csv', index=False)
        
    
def main():
    '''
    Grabs necessary SVN data from folders and then calls to write to the csv
    '''
    args = parse_args()
    three_sla, dead_sla = load_default_sla(CONFIG_FILE)
    df = create_dataframe(three_sla, dead_sla)
    write_to_csv(df, args.file)

if __name__ == "__main__":
    main()
