'''
Programmatically create DOI for a Synapse project
'''
import os
import requests
import synapseclient
from synapseclient import Project, Folder, File
import yaml

def synapse_login():
    '''
    Log-in to Synapse using shared SIBIS credentials
    '''
    syn = synapseclient.Synapse()
    config = yaml.load(open(os.path.join(os.path.expanduser("~"),
                                         ".sibis-general-config.yml")))
    syn.login(email=config.get('synapse').get('user'),
              password=config.get('synapse').get('password'))
    return syn

def main():
    '''
    Set up synapse client, connect to correct info, etc.
    '''
    syn_client = synapse_login()

if __name__ == '__main__':
    main()
