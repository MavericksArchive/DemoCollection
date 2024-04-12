"""
This function is for the papyrus regex/solution generation module.

It requires and assumes that the corresponding docker containers are running.
"""
import json
from typing import List, Dict 
import http.client


def run_papyrus_release(user_input: str, nodes_run_data: List) -> Dict:
    """
    Invoke the papyrus regex/solution generation module that is 
    running.
    
    :param user_input:
    :param nodes_run_data: not used ...
    :return regex_sol_output: 
    """    
    # Set up the headers
    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': '230e2b5e-fb08-405c-b9d2-f17e66be3b47'
    }
    
    # Set up the request body
    payload = {
        'user_input': user_input,
        'nodes_run_data': []  # hardcoded
    }

    # Send a POST request with JSON payload
    
    # (a) development server
    # conn = http.client.HTTPConnection('ip-10-0-0-89.us-west-2.compute.internal:2222')

    # (b) dedicated server
    conn = http.client.HTTPConnection('ip-10-0-0-93.us-west-2.compute.internal:2222')
    
    # Convert your payload to a JSON string and then bytes
    payload_bytes = json.dumps(payload).encode('utf-8')
    print(payload_bytes)

    # Make a POST request with your payload
    print('conn.requesting...')
    conn.request("POST", "papyrusGen", body=payload_bytes, headers=headers)
    print('conn.request successful!')
    
    response = conn.getresponse()
    response_data = response.read()
    print('response.read() successful!')

    # Optionally, convert byte data to JSON
    print(f'type(response_data): {type(response_data)}')
    print(f'response_data: {response_data}')
    data_json = json.loads(response_data.decode("utf-8"))
    
    regex_sol_output = {
        'intention': json.dumps(data_json.get('intention')),
        'user_response': json.dumps({'regex': data_json.get('user_response').get('regex')}) 
    }
    return regex_sol_output
    