'''
Programmatically create DOI for a Synapse project
'''
import json
import os
import requests
import synapseclient
from synapseclient import Project, Folder, File
import yaml

''' Constants '''
OBJECT_ID = 'syn25191261'

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

def get_entity_properties(syn, object_id):
    '''
    Get properties of current Synapse object, given current Synapse ID
    '''
    entity = syn.get(object_id)
    return entity.properties

def create_doi(syn_client, file_path):
    '''
    Read in JSON from file and generate DOI programmatically
    '''
    f = open(file_path, 'r')
    test_send_body = json.load(f)
    send_body = json.dumps(test_send_body)
    response = syn_client.restPOST('https://repo-prod.prod.sagebase.org/repo/v1/doi/async/start', send_body)
    return response

def main():
    '''
    Set up synapse client, connect to correct info, etc.
    '''
    syn_client = synapse_login()
    initial_props = get_entity_properties(syn_client, OBJECT_ID)
    token_number = create_doi(syn_client, 'test_doi.json')

if __name__ == '__main__':
    main()
