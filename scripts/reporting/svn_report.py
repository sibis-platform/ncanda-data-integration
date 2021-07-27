'''
This file creates a .csv file containing the name of each laptop and its last changed date
'''
import argparse
import csv
from datetime import datetime, timezone
import os
import svn.local
import pandas as pd

'''
Constants -- paths for reports, default save names, SLA, columns, and sites
TO-DO: Change SLA_DAYS to a parser arg?
'''
REPORTS_DIR = '/fs/storage/laptops/ncanda'
DEFAULT_CSV = '/fs/ncanda-share/log/status_reports/'
SLA_DAYS = 30
DATA_COLUMNS = ['laptop', 'date_updated', 'time_diff', 'sla', 'sla_percentage']
SITES = ['duke', 'sri', 'ohsu', 'upmc', 'ucsd']

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

def create_dataframe():
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
            sla_percentage = time_diff.total_seconds() / (SLA_DAYS * 24 * 60 * 60)
            new_row = {
                'laptop': directory,
                'date_updated': mod_time,
                'time_diff': time_diff,
                'sla': SLA_DAYS,
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
    df = create_dataframe()
    write_to_csv(df, args.file)

if __name__ == "__main__":
    main()
