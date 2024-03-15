"""
Prerequisites:
 - Please make sure that those contiainers are runnining.

How to invoke:

## with debug is False
curl -X POST 'http://ip-10-0-0-93.us-west-2.compute.internal:2222/papyrusGen?conversation_id=25141c36-9622-4726-a4fa-04d7d6403a45\&message_id=81764c5d-920c-4cbf-a3e8-f04ea26e5790&source=netlens\&dryrun=True\&debug=False' -H 'Content-Type: application/json' -d '{"user_text": "One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. I have noticed that the pubd process is consuming the majority of memory.  Is this a bug?", "nodes_run_data": []}'


# with debug is True
curl -X POST 'http://ip-10-0-0-93.us-west-2.compute.internal:2222/papyrusGen?conversation_id=25141c36-9622-4726-a4fa-04d7d6403a45\&message_id=81764c5d-920c-4cbf-a3e8-f04ea26e5790&source=netlens\&dryrun=True\&debug=True' -H 'Content-Type: application/json' -d '{"user_text": "One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. I have noticed that the pubd process is consuming the majority of memory.  Is this a bug?", "nodes_run_data": []}'


POST body:
{
    "user_text": "One of our network management systems has shown that memory utilization for the device …. Is this a bug?", 
    "nodes_run_data": []  # empty
} 


Output expected:
{
    "conversation_id": "25141c36-9622-4726-a4fa-04d7d6403a45",     
    "message_id": "81764c5d-920c-4cbf-a3e8-f04ea26e5790",          
    "user_response": "<Papyrus output>", 
    "nodes_run_cmds": {}.  # empty
}
"""

import json
import time

import requests
from flask import Flask, request, jsonify


app = Flask(__name__)


def make_request_call(url, headers, payload, method='POST'):
    json_payload = json.dumps(payload)

    if method == 'POST':
        response = requests.post(url, headers=headers, data=json_payload)
    else:
        raise NotImplementedError

    if response.status_code == 200:
        print('Request successful!')
        print(response.json())
    else:
        print('Request failed!')
        print(response.text) 
            
    return response


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
    response = make_request_call(url, headers, payload)
    return response

        
def run_intention_module(topic_output):
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
    response = make_request_call(url, headers, payload)
    return response


def run_papyrus_module(topic_output, intention_output):
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
    response = make_request_call(url, headers, payload)
    return response    


@app.route('/papyrusGen', methods=['POST'])
def testPipeline():
    """
    """
    timer_start = time.time()

    ## =======================================================
    ## Input parsing
    ## =======================================================
    # parse params 
    params = request.args.to_dict()
    params = {str(k).strip('\\'): str(v).strip('\\') for k, v in params.items()}
    conversation_id = params.get('conversation_id', 'placeholder_conv_id')
    message_id = params.get('message_id', 'placeholder_message_id')
    source = params.get('source', 'placeholder_source')
    dryrun = params.get('dryrun', 'placeholder_dryrun')
    debug = params.get('debug', 'placeholder_debug')
    
    # parse body
    raw_query = request.get_json(force=True)
    user_input_body = raw_query.get('user_text', '')
    nodes_run_data_body = raw_query.get('nodes_run_data', [])

    ## =======================================================
    ## Topic module 
    ## =======================================================
    topic_output = run_topic_module(user_input=user_input_body)
    time_topic_module = time.time()-timer_start
    print(f"topic module takes {time_topic_module}")
    # topic_output = topic_output['message']
    topic_output_message = json.loads(topic_output.text).get('message')
    try:
        # double json.loads....
        topic_output_json = json.loads(json.loads(topic_output_message))   # json output
    except Exception as errmsg:
        print(f'!!! ERRROR in topic_output !!! {errmsg}')
        raise 
 
    # formatting the output
    topic_output_json['user_input_desc'] = topic_output_json[
        'user_input_desc'].replace('\nUSER:', '').replace('USER: ', '')
    
    ## =======================================================
    ## BI/CE module 
    ## =======================================================
    # intention_output = run_intention_module(topic_output)
    intention_output = run_intention_module(topic_output_json)     # json input
    time_intention_module = time.time()-timer_start-time_topic_module
    print(f"intention module takes {time_intention_module}")
    intention_output = json.loads(intention_output.text)['message'][0]
    
    ## =======================================================
    ## Papyrus module 
    ## =======================================================
    # papyrus_output = run_papyrus_module(topic_output, intention_output)
    papyrus_output = run_papyrus_module(topic_output_json, intention_output)
    time_papyrus_module = time.time()-timer_start-time_topic_module-time_intention_module
    print(f"papyrus module takes {time_papyrus_module}")
    print(json.loads(papyrus_output.text)['message'])

    # the output format
    ## =======================================================
    ## Output formatting
    ## =======================================================
    try:
        if str(debug) == 'True':
            pipeline_output = {
                "conversation_id": conversation_id,     # pass through
                "message_id": message_id,               # pass through 
                # "user_response": json.loads(papyrus_output.text)['message'], 
                "user_response": json.dumps(json.loads(papyrus_output.text)['message']),
                "nodes_run_cmds": {},                                          # empty,
                "[DEBUG] source": source,
                "[DEBUG] dryrun": str(dryrun),
                "[DEBUG] debug": str(debug),
                "[DEBUG] user_input": user_input_body,
                "[DEBUG] nodes_run_data": nodes_run_data_body,
            }
        else:
            pipeline_output = {
                "conversation_id": conversation_id,     # pass through
                "message_id": message_id,               # pass through 
                # "user_response": json.loads(papyrus_output.text)['message'], 
                "user_response": json.dumps(json.loads(papyrus_output.text)['message']),
                "nodes_run_cmds": {}                                          # empty
            }
        # import pdb; pdb.set_trace()
        return jsonify(pipeline_output), 200
    except:
        error_body = {'message': 'error....'}
        return jsonify(error_body), 422
    
    
if __name__ == "__main__":
    # testPipeline()
    app.run(debug=True, host='0.0.0.0', port=2222)