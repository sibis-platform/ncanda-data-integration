'''
Gets timestamps for the REDCap All Forms Dashboard
'''
import sibispy
import sys

# Path to store timestamp csv files
PATH='/fs/ncanda-share/log/status_reports/inventory_dates/'

def main():
    '''
    Sets up and configures sessions, passes in to get al correspoding .csv files
    '''
    events = []
    # Connect to a Sibispy Session
    session = sibispy.Session()
    if not session.configure():
        raise RuntimeError("sibispy is not configured; aborting!")
        sys.exit(1)
    api = session.connect_server('data_entry')

    # Get the data, add event name as column, and generate corresponding events
    data_entry = api.export_records(format='df', fields=['visit_date'])
    data_entry['redcap_name'] = data_entry.index.get_level_values('redcap_event_name')
    events = data_entry.index.get_level_values('redcap_event_name').unique().tolist()
    
    # Iterate through each event, find all columns with event name, and create CSV
    for event in events:
        event_subset = data_entry[data_entry['redcap_name'] == event].drop(columns=['redcap_name'])
        event_subset.to_csv(PATH + event + '.csv')
        
if __name__ == "__main__":
    main()
