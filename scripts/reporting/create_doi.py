'''
Programmatically create DOI for a Synapse project
'''
import argparse
import json
import os
import requests
import yaml

def parse_args(arg_input=None):
    '''
    Set up parser arguments
    '''
    parser = argparse.ArgumentParser(
        description="Programmatically generate DOI for given synapse ID and JSON file")
    parser.add_argument(
        "--id",
        help="Synapse ID to change",
        action="store")
    parser.add_argument(
        "--file",
        help="JSON file with DOI info",
        action="store")
    return parser.parse_args(arg_input)

def synapse_login():
    '''
    Get Oauth2 Access Token for Synapse
    '''
    # Get shared log-in credentials
    config = yaml.load(open(os.path.join(os.path.expanduser("~"),
                                         ".sibis-general-config.yml")))

    # Necessary request info - URL, payload, and headers
    login_url = "https://repo-prod.prod.sagebase.org/auth/v1/login2"
    payload = json.dumps({
        "username": config.get('synapse').get('user'),
        "password": config.get('synapse').get('password')
    })
    headers = {
        'Content-Type': 'application/json',
    }
    
    # Create and return response
    response = requests.request("POST", login_url, headers=headers, data=payload)
    return response.json()['accessToken']

def get_entity_properties(object_id):
    '''
    Get properties of current Synapse object, given current Synapse ID
    '''
    # Necessary request info - URL and headers (no payload)
    doi_data_url = 'https://repo-prod.prod.sagebase.org/repo/v1/doi?id=' + str(object_id) + '&type=ENTITY'

    # Create and return response
    response = requests.request("GET", doi_data_url)
    return response.json()['etag']

def create_doi(object_id, access_token, etag, file_path):
    '''
    Read in JSON from file and generate DOI programmatically
    '''
    # Get data from JSON file and update with proper object ID and etag
    f = open(file_path, 'r')
    send_body = json.load(f)
    send_body['doi']['objectId'] = object_id
    send_body['doi']['etag'] = etag

    # Necessary request info - URL, payload, and headers
    create_url = "https://repo-prod.prod.sagebase.org/repo/v1/doi/async/start"
    payload = json.dumps(send_body)
    headers = {
        'Authorization': 'Bearer ' + str(access_token),
        'Content-Type': 'application/json',
    }

    # Create and return response
    response = requests.request("POST", create_url, headers=headers, data=payload)
    return response.json()['token']

def get_creation_info(access_token, token_number):
    '''
    Get callback info from POST request from token number
    '''
    # Neceessary request info - URL and headers (no payload)
    get_data_url = "https://repo-prod.prod.sagebase.org/repo/v1/doi/async/get/" + str(token_number)
    headers = {
        'Authorization': 'Bearer ' + str(access_token),
        'Content-Type': 'application/json',
    }

    # Create and return response
    response = requests.request("GET", get_data_url, headers=headers)
    return response.json()

def main():
    '''
    Set up synapse client, connect to correct info, etc.
    '''
    args = parse_args()
    access_token = synapse_login()
    etag = get_entity_properties(args.id)
    token_number = create_doi(args.id, access_token, etag, args.file)
    entity_data = get_creation_info(access_token, token_number)
    print(entity_data)

if __name__ == '__main__':
    main()
