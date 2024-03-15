"""
POST body:
{
    "user_text": "One of our network management systems has shown that memory utilization for the device …. Is this a bug?", 
    "nodes_run_data": []  # empty
} 

Output expected:
{
    "conversation_id": "25141c36-9622-4726-a4fa-04d7d6403a45",     # cook up some uuid. Can be anything ID that is given to us 
    "message_id": "81764c5d-920c-4cbf-a3e8-f04ea26e5790",          # cook up some uuid. Can be anything ID that is given to us
    "user_response": "<Papyrus output.. currently they say it's a string>", 
    "nodes_run_cmds": {}.                                          # empty
}

Depending on the input we can leverage below to parse the params. This is from AWS Lambda: project-x-be-test-request

# this structure works for API Gateway and Lambda (proxy used). 
# For the demo.. we can design the event as we want. 
def parse_query_param(event):
    # Parsing the query params

    def parse_single_param(event, query_key):
        value = None
        try:
            if (event['queryStringParameters']) and (event['queryStringParameters'][query_key]) and (
                    event['queryStringParameters'][query_key] is not None):
                value = event['queryStringParameters'][query_key]
        except KeyError:
            print(f'No query_key: {query_key}')
        return value

    conversation_id = parse_single_param(event, query_key='conversation_id')
    message_id = parse_single_param(event, query_key='message_id')
    source = parse_single_param(event, query_key='source')
    dryrun = parse_single_param(event, query_key='dryrun')
    debug = parse_single_param(event, query_key='debug')
    
    # skipped type checking
    return {'conversation_id': conversation_id, 'message_id': message_id, 'source': source, 'dryrun': dry_run_eval, 'debug': debug_eval}
"""

import os
import sys 
import json
import time

import requests
from flask import Flask, request, jsonify


# app = Flask(__name__)

USER_INPUT = {"user_input": "One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. \
             When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. \
            I have noticed that the 'pubd' process is consuming the majority of memory. Is this a bug?"}


tmp = 'One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. I have noticed that the pubd process is consuming the majority of memory.  Is this a bug?'

def run_topic_module(user_input=None):

    # Set up the URL
    url = 'http://localhost:8888/dev'

    # Set up the headers
    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': '230e2b5e-fb08-405c-b9d2-f17e66be3b47'
    }

    # Set up the request body
    payload = {
        'user_input': user_input
    }

    json_payload = json.dumps(payload)

    # Make the POST request
    response = requests.post(
        url, 
        headers=headers, data=json_payload)

    # Check the response
    if response.status_code == 200:
        print('Request successful!')
        print(response.json())
    else:
        print('Request failed!')
        print(response.text) 
    
        
    # inspect the outpu
    return response
        

def run_intention_module(topic_output):

    import json 
    import requests

    # Set up the URL
    url = 'http://localhost:8089/query'

    # Set up the headers
    headers = {
        'Content-Type': 'application/json',
    }

    # Set up the request body
    payload = {
        # 'question': topic_output['user_input_desc']['user_input']
        'question': topic_output['user_input_desc']
    }

    json_payload = json.dumps(payload)

    # Make the POST request
    response = requests.post(
        url, 
        headers=headers, data=json_payload)

    # Check the response
    if response.status_code == 200:
        print('Request successful!')
        print(response.json())
    else:
        print('Request failed!')
        print(response.text) 
    

    return response

def run_papyrus_module(topic_output, intention_output):
    # papyrus_input= {'user_input_desc': topic_output['user_input_desc'], 'page_content': intention_output['page_content']}

    # cmd = f'curl -X POST http://localhost:5000/generate -H "Content-Type: application/json" -d {papyrus_input}'

    # return_papyrus_dict = sys.run(cmd)

    # Set up the URL
    url = 'http://localhost:8090/generate'

    # Set up the headers
    headers = {
        'Content-Type': 'application/json',
    }

    # Set up the request body
    payload = {
        'user_input_desc': topic_output['user_input_desc'],
        'page_content': intention_output['page_content']
    }

    json_payload = json.dumps(payload)

    # Make the POST request
    response = requests.post(
        url, 
        headers=headers, data=json_payload)

    # Check the response
    if response.status_code == 200:
        print('Request successful!')
        print(response.json())
    else:
        print('Request failed!')
        print(response.text) 

    return response    


# @app.route('/papyrusGen', methods=['POST'])
def testPipeline():
    """
    This is to show how to use this class.    
    """
    timer_start = time.time()

    # parse params 
    conversation_id= 'placeholder_conv_id'
    message_id = 'placeholder_msg_id'

    # raw_query = request.get_json(force=True)
    # print(f'{raw_query}')

    raw_query = {"user_input": "One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. I have noticed that the 'pubd' process is consuming the majority of memory.  Is this a bug?"}

    topic_output = run_topic_module(user_input=raw_query['user_input'])
    print(f'topic output is {topic_output}')

    
    time_topic_module = time.time()-timer_start

    print(f"topic module takes {time_topic_module}")
    # topic_output = topic_output['message']
    topic_output = json.loads(json.loads(json.loads(topic_output.text)['message']))
    # topic_output = json.loads(topic_output.text)['message']

    # import pdb; pdb.set_trace()

    intention_output = run_intention_module(topic_output)
    time_intention_module = time.time()-timer_start-time_topic_module
    print(f"intention module takes {time_intention_module}")

    intention_output = json.loads(intention_output.text)['message'][0]
    
    
    papyrus_output = run_papyrus_module(topic_output, intention_output)
    time_papyrus_module = time.time()-timer_start-time_topic_module-time_intention_module
    print(f"papyrus module takes {time_papyrus_module}")
    print(json.loads(papyrus_output.text)['message'])

    
    # the output format
    # pipeline_output = {
    #     "conversation_id": conversation_id,     # pass through
    #     "message_id": message_id,               # pass through 
    #     "user_response": "<Papyrus output.. currently they say it's a string>", # <-- replace with the real papyrus_output
    #     "nodes_run_cmds": {}                                          # empty
    # }
    return topic_output

    
if __name__ == "__main__":
    testPipeline()
    # app.run(debug=True, host='0.0.0.0', port=2222)