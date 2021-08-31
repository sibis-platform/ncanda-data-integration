'''
Gets timestamps for the REDCap All Forms Dashboard
'''
import sibispy
import sys

'''
All arms necessary for getting all the dates
'''
arms = ['18month_followup_arm_1', '4y_visit_arm_1', '78month_followup_arm_1', '1y_visit_arm_1', '54month_followup_arm_1', '7y_visit_arm_1', '2y_visit_arm_1', '5y_visit_arm_1', '8y_visit_arm_1', '30month_followup_arm_1', '66month_followup_arm_1', '90month_followup_arm_1', '3y_visit_arm_1', '6month_followup_arm_1', 'baseline_visit_arm_1', '42month_followup_arm_1', '6y_visit_arm_1']

PATH='/fs/ncanda-share/log/status_reports/inventory_dates/'

def main():
    '''
    Sets up and configures sessions, passes in to get al correspoding .csv files
    '''
    session = sibispy.Session()
    if not session.configure():
        raise RuntimeError("sibispy is not configured; aborting!")
        sys.exit(1)
    api = session.connect_server('data_entry')
    for arm in arms:
        print(arm)
        data_entry = api.export_records(format='df', fields=['visit_date'], events=[arm])
        data_entry.to_csv(PATH + arm + '.csv')
main()
