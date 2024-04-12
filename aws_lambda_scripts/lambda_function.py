"""
This Lambda is for the `/request` 

https://dm9cqra0dzwbk.cloudfront.net/netlens-api/ai/v1/docs#/

It requires and assumes that the corresponding docker containers are running.
"""
import ast
import json


from papyrus_model_call import run_papyrus_release


def parse_query_param(event):
    """
    Parsing the query params.
    
    :param event:
    :return parsed_query_param
    """

    def _parse_single_param(event, query_key):
        """
        :param event:
        :param query_key:
        :return value:
        """
        value = None
        try:
            if (event['queryStringParameters']) and (event['queryStringParameters'][query_key]) and (
                    event['queryStringParameters'][query_key] is not None):
                value = event['queryStringParameters'][query_key]
        except KeyError:
            print(f'No query_key: {query_key}')
        return value

    conversation_id = _parse_single_param(event, query_key='conversation_id')
    message_id = _parse_single_param(event, query_key='message_id')
    source = _parse_single_param(event, query_key='source')
    dryrun = _parse_single_param(event, query_key='dryrun')
    debug = _parse_single_param(event, query_key='debug')
    
    if dryrun:
        dry_run_eval = ast.literal_eval(dryrun.strip().title())
        if not isinstance(dry_run_eval, bool):
            raise Exception('dry_run value not boolean')
        
    if debug:
        debug_eval = ast.literal_eval(debug.strip().title())
        if not isinstance(debug_eval, bool):
            raise Exception('dry_run value not boolean')

    if dryrun and debug:
        parsed_query_param = {
            'conversation_id': conversation_id, 
            'message_id': message_id, 
            'source': source, 
            'dryrun': dry_run_eval, 
            'debug': debug_eval
        }
        return parsed_query_param
    else:
        parsed_query_param = {
            'conversation_id': conversation_id, 
            'message_id': message_id, 
            'source': source, 
            'dryrun': 'placeholder_dryrun', 
            'debug': 'placeholder_debug'
        }
        return parsed_query_param


def parse_body(event):
    """
    Parse the query body.
    
    :param event:
    :return parsed_body:
    """
    user_input = 'placeholder_user_input'
    body = None
    nodes_body = []

    try:
        if (event['body']) and (event['body'] is not None):
            if isinstance(event['body'], dict):
                body_json_str = json.dumps(event['body'])
            else:
                body_json_str = event['body']

            body = json.loads(body_json_str)
            print('Successfully parse the body')            
    except KeyError:
        print('Failed parsing the body')
    
    if not body:
        raise Exception('MissingBody: the body does not exist!')
    
    # user text
    try:
        if (body['user_input']) and (body['user_input'] is not None):
            user_input = body['user_input']
            print(f'user_input: {user_input}')
    except KeyError:
        print('No user_input')
            
    # nodes 
    try:
        nodes_body = body['nodes_run_data']
    except KeyError:
        print('no nodes')

    # TODO: what do we do with the nodes_body?            

    parsed_body = {'user_input': user_input, 'nodes_body': nodes_body}
    return parsed_body


def run_nodes_run_cmds():
    """
    Mock data for the nodes_run_cmds. This was supposed to be an output 
    from the model, asking the backend to run the common/specific "show" 
    commands against the certain set of devices.
    
    :return nodes_run_cmds: mock data
    """
    nodes_run_cmds = {
        "nodes_run_common_cmds": {
          "node_ids": ["node1", "node2"],
          "commands": ["show version", "show running-config"]
        },
        "nodes_run_specific_cmds": [
          {
            "node_id": "node1",
            "commands": ["show scp"]
          }
        ]
    }
    return nodes_run_cmds


def lambda_handler(event, context):
    """
    The main lambda function, following the Runtime setting.
    Handler = lambda_function.lambda_handler.
    
    :param event:
    :param context:
    :return res:
    """
    # parse the query params
    params = parse_query_param(event)
    
    # unique conversation id 
    conversation_id = params.get('conversation_id') if params.get('conversation_id') else 'placeholder_conv'

    # A unique message id to track the users request
    message_id = params.get('message_id') if params.get('message_id') else 'placeholder_msg'

    # Source making the request. Default value : netlens
    source = params.get('source') if params.get('source') else 'placeholder_source'
    
    # Set the dryrun flag to true if you simply want to validate the workflow with mock data. Default value: netlens
    dryrun = params.get('dryrun') # if params.get('dryrun') else True
    
    # Enable debug mode. Default value: False
    debug = params.get('debug') # if params.get('debug') else True

    # parse the body
    body = parse_body(event)
    user_input = body['user_input'] if body['user_input'] else 'placeholder_user_input'
    nodes_body = body['nodes_body'] if body['nodes_body'] else 'placeholder_nodes_body'

    # process 
    print('processing ... ')
    # nodes_run_cmds = run_nodes_run_cmds(body)
    nodes_run_cmds = []  ## mock this portion now with an empty list (less confusing...)
    
    if str(dryrun).lower() == 'true':
        user_response = {"regex": "mock_dryrun", "solution": "mock_dryrun", "workaround": "mock_dryrun"} 
        intention = {"goal": "mock_dryrun", "main_question": "mock_dryrun", "major_problem": "mock_dryrun"}
    else:
        print(f'Trying to tap the EC2 ... ')
        response = run_papyrus_release(user_input=user_input, nodes_run_data=nodes_body)
        user_response = response['user_response']# .text
        intention = response['intention']
        print(user_response)
        print(f'Successfully tapped the EC2')
            
    # return
    try:
        if debug:
            success_body = {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "user_response": user_response,
                    "nodes_run_cmds": nodes_run_cmds,
                    "intention": intention,
                    "[Debug] source": source,
                    "[Debug] dryrun": dryrun,
                    "[Debug] debug": debug,
                    "[Debug] user_input": user_input,
                    "[Debug] nodes_body": nodes_body
                }
        else:
            success_body = {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "intention": intention,
                    "user_response": user_response,
                    "nodes_run_cmds": nodes_run_cmds
            }
    
        res = {
            "statusCode": 200,
            "body": json.dumps(success_body)
        }
    except:
        error_body = {
          "detail": [
            {
              "loc": [
                "string"
              ],
              "msg": "string",
              "type": "string"
            }
          ]
        }
        res = {
            "statusCode": 422,
            "body": json.dumps(error_body)
        }

    return res
    
