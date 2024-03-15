import time
import datetime
import json 
from tqdm import tqdm 
import pandas as pd
import requests 
from typing import Dict


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

def run_papyrus(user_input: str) -> requests.Response:
    """
    Do the POST call to the AI endpoint in AWS.
    
    :param user_input: user input text
    :return response: response from the endpoint
    """
    api_endpoint = 'http://ip-10-0-0-93.us-west-2.compute.internal:7356/dev'
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': '230e2b5e-fb08-405c-b9d2-f17e66be3b47'
    }
    payload = {'user_input': user_input}
    response = make_request_call(api_endpoint, headers, payload, method='POST')
    return response
    
    
def run_one_inference(use_case=1):
    start_time = time.time()
    if use_case == 1:
        # user_input = "One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. I have noticed that the 'pubd' process is consuming the majority of memory.  Is this a bug?" 
        user_input = "One of our network management systems has shown that memory utilization for a cat9200 switched named MRE-Edge2.cisco.com has been increasing. The device is attempting to send telemetry data to DNAC but the connection never establishes. I have noticed that the pubd process is consuming the majority of memory. The device is trying to send telemetry data to our DNAC, but it seems the receiver is responding with a device not found.  Is this a bug"
    elif use_case == 2:
        user_input = "I have 187 devices that show as potentially vulnerable to the PSIRT cisco-sa-iosxe-webui-privesc-j22SaA4z. How can I confirm vulnerability to this PSIRT that allows a remote, unauthenticated attacker to create an account on an affected device with privilege level 15 access and can then use that account to gain control of the affected device?"
    response = run_papyrus(user_input)
    response.raise_for_status()
    time_elapsed = time.time() - start_time
    return time_elapsed, response


def main(no_of_test, use_case):
    now = datetime.datetime.now()
    test_time = now.strftime('%Y%m%d_%H%M%S')
    res = []
    for i in tqdm(range(no_of_test)):
        time_elapsed, response = run_one_inference(use_case)
        output_json = json.loads(response.text, object_hook=flatten_hook)
        intention = json.loads(output_json['message'])
        output = {'latency_seconds': str(time_elapsed),'goal': intention["goal"], 'main_question': intention["main_question"],'major_problem': intention["major_problem"],'extracted_entity': intention["extracted_entity"],"system_message": intention["system_message"],"steps": intention["steps"],"solutions": intention["solutions"],}
        res.append(output)
        time.sleep(3)
    
    df = pd.DataFrame(res)
    print(df.head())
    df.to_csv(f'temp_test_usecase_{str(use_case)}_{str(no_of_test)}_tests_at_{test_time}.csv')
    return df


if __name__ == "__main__":
    main(no_of_test=30, use_case=1)
