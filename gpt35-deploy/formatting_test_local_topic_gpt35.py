"""
This is to show how to call, the AI endpoint output, parse/write to a JSON file, 
and also read the JSON file written.

1. The function `call_and_write`: 
    Call the AI endpoint and write a JSON file to a filesystem

2. The function `read_json_file`: 
    Read the JSON file

How to run:
    python formatting_test_topic_gpt35.py
"""
import json
import pprint
from typing import Dict
import requests


def call_and_write(user_input: str, output_json: str = 'topic_gpt35_output.json') -> None:
    """
    Call the topic_gpt35 and write to a JSON file
    
    :param user_input: user input text 
    :param output_json: JSON file to write
    """
    response = run_topic_gpt35(user_input)
    response.raise_for_status()
    
    # topic module
    topic_output_message = json.loads(response.text).get('message')
    topic_output_json = json.loads(json.loads(topic_output_message))
    
    with open(output_json, 'w') as f:
        json.dump(topic_output_json, f)
        
    pprint.pprint(topic_output_json) 
    print(f'Successfully wrote the JSON file')
    print('Finished writing!')
    print('Check the JSON file! topic_gpt35_output.json')


def read_json_file(input_json :str = 'topic_gpt35_output.json') -> None:
    """
    Read the JSON file as a Python Dictionary 
    
    :param input_json: JSON file to read
    """
    print(f'Reading the JSON file... ')
    with open(input_json, 'r') as f:
        data = json.load(f)
    print(f'Read the JSON successfully')
    print(f'type(data): {type(data)}')
    print(f'data.keys(): {data.keys()}')
    pprint.pprint(data)
    
    # the below is just printing, showing they are 
    # valid JSON file, valid Python lists and dictionaries...
    print(f'=====' * 20)
    print(f'Please note the following items')
    for k, v in data.items():
        if k == 'intention':
            for subk, subv in v.items(): 
                if subk in ['steps', 'solutions']:
                    for idx, item in enumerate(subv, 1):
                        print(f'    <intention> {subk}: #{idx}. {item}')
                else:
                    print(f'    <intention> {subk}: {subv}')
        elif k == 'user_response':
            for subk, subv in v.items(): 
                print(f'    <user_response> {subk}: {subv}')
        else:
            print(f'{k}: {v}')
    print(f'=====' * 20)
    print('Finished reading!')
        
        
def run_topic_gpt35(user_input: str) -> requests.Response:
    """
    Do the POST call to the AI endpoint in AWS.
    
    :param user_input: user input text
    :return response: response from the endpoint
    """
    api_endpoint = 'http://ip-10-0-0-93.us-west-2.compute.internal:8888/dev'
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': '230e2b5e-fb08-405c-b9d2-f17e66be3b47'
    }
    payload = {'user_input': user_input}
    response = make_request_call(api_endpoint, headers, payload, method='POST')
    return response


def make_request_call(
    api_endpoint: str, headers: Dict, payload: Dict = None, 
    params: Dict = None, method: str ='GET'
    ) -> requests.Response:
    """
    :param api_endpoint: Papyrus API endpoint
    :param headers: API header
    :param payload: API payload
    :param params: API params
    :param method: API method
    :return response: API response
    """
    if payload:
        json_payload = json.dumps(payload)

    if method == 'GET':
        response = requests.get(api_endpoint, headers=headers)
    elif method == 'POST':
        response = requests.post(
            api_endpoint, headers=headers, data=json_payload, params=params)
    else:
        raise NotImplementedError

    if response.status_code == 200:
        print('Request successful!')
        # print(response.json())
    else:
        print('Request failed!')
        # print(response.text) 
            
    return response


def flatten_hook(obj):
    """object hook function for json.loads"""
    for key, value in obj.items():
        if isinstance(value, str):
            try:
                obj[key] = json.loads(value, object_hook=flatten_hook)
            except ValueError:
                pass
    return obj
    

def main():    
    # this is the user input
    # user_input = "I have 187 devices that show as potentially vulnerable to the PSIRT cisco-sa-iosxe-webui-privesc-j22SaA4z. How can I confirm vulnerability to this PSIRT that allows a remote, unauthenticated attacker to create an account on an affected device with privilege level 15 access and can then use that account to gain control of the affected device?" 
    # user_input = "One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. I have noticed that the 'pubd' process is consuming the majority of memory.  Is this a bug?" 
    user_input = "One of our network management systems has shown that memory utilization for a cat9200 switched named dtw-302-9300-sw-1 has been increasing. The device is attempting to send telemetry data to DNAC but the connection never establishes. I have noticed that the pubd process is consuming the majority of memory. The device is trying to send telemetry data to our DNAC, but it seems the receiver is responding with a device not found. Today the switch had a log about memory value exceeding 90%. Is this a bug?"
    
    # call the AI endpoint and write a JSON file
    call_and_write(user_input)
    # read the output 
    read_json_file()
    print('Done')

if __name__ == "__main__":
    main()
