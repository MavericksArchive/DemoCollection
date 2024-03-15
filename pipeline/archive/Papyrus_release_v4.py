
# please look at the pipeline_deploy/Papyrus_release_v4.py



# """
# Need to add the following in the requirements.txt
# marshmallow==3.21.0


# Prerequisites:
#  - Please make sure that those contiainers are runnining.

# How to invoke:

# ## 1st use case, with debug is False
# curl -X POST 'http://ip-10-0-0-93.us-west-2.compute.internal:2222/papyrusGen?conversation_id=25141c36-9622-4726-a4fa-04d7d6403a45\&message_id=81764c5d-920c-4cbf-a3e8-f04ea26e5790&source=netlens\&dryrun=True\&debug=False' -H 'Content-Type: application/json' -d '{"user_text": "", "nodes_run_data": []}'
# curl -X POST 'http://ip-10-0-0-89.us-west-2.compute.internal:2222/papyrusGen?conversation_id=25141c36-9622-4726-a4fa-04d7d6403a45\&message_id=81764c5d-920c-4cbf-a3e8-f04ea26e5790&source=netlens\&dryrun=True\&debug=False' -H 'Content-Type: application/json' -d '{"user_text": "", "nodes_run_data": []}'


# # 1st use case, with debug is True
# curl -X POST 'http://ip-10-0-0-93.us-west-2.compute.internal:2222/papyrusGen?conversation_id=25141c36-9622-4726-a4fa-04d7d6403a45\&message_id=81764c5d-920c-4cbf-a3e8-f04ea26e5790&source=netlens\&dryrun=True\&debug=True' -H 'Content-Type: application/json' -d '{"user_text": "", "nodes_run_data": []}'
# curl -X POST 'http://ip-10-0-0-89.us-west-2.compute.internal:2222/papyrusGen?conversation_id=25141c36-9622-4726-a4fa-04d7d6403a45\&message_id=81764c5d-920c-4cbf-a3e8-f04ea26e5790&source=netlens\&dryrun=True\&debug=True' -H 'Content-Type: application/json' -d '{"user_text": "", "nodes_run_data": []}'


# # 2nd use case... with debug is True
# curl -X POST 'http://ip-10-0-0-93.us-west-2.compute.internal:2222/papyrusGen?conversation_id=25141c36-9622-4726-a4fa-04d7d6403a45\&message_id=81764c5d-920c-4cbf-a3e8-f04ea26e5790&source=netlens\&dryrun=True\&debug=True' -H 'Content-Type: application/json' -d '{"user_text": "", "nodes_run_data": []}'
# curl -X POST 'http://ip-10-0-0-89.us-west-2.compute.internal:2222/papyrusGen?conversation_id=25141c36-9622-4726-a4fa-04d7d6403a45\&message_id=81764c5d-920c-4cbf-a3e8-f04ea26e5790&source=netlens\&dryrun=True\&debug=True' -H 'Content-Type: application/json' -d '{"user_text": "", "nodes_run_data": []}'


# POST body:
# {
#     "user_text": "One of our network management systems has shown that memory utilization for the device …. Is this a bug?", 
#     "nodes_run_data": []  # empty
# } 


# Output example:
# {
#     'conversation_id': 'conv123',
#     'intention': {'extracted_entity': ['ext_ent'],
#                 'goal': 'myGoal',
#                 'main_question': 'myMainQuestion',
#                 'major_problem': 'myMajorProblem',
#                 'solutions': ['solution1', 'solution2', 'solution3'],
#                 'steps': ['step1', 'step2', 'step3'],
#                 'system_message': ['sys_msg']},
#     'message_id': 'msg0000',
#     'nodes_run_cmds': [],
#     'user_response': {'regex': 'myRegex',
#                     'solution': 'mySolution',
#                     'workaround': 'myWorkaround'}
# }
# """
# import ast 
# import json
# import time

# import requests
# from flask import Flask, request, jsonify
# from marshmallow import Schema, fields


# class IntentionSchema(Schema):
#     goal = fields.Str()
#     main_question = fields.Str()
#     major_problem = fields.Str()
#     situation = fields.Str()
#     summary = fields.Str()
#     extracted_entity = fields.List(fields.Str())
#     system_message = fields.List(fields.Str())
#     steps = fields.List(fields.Str())
#     solutions = fields.List(fields.Str())

        
# class PapyrusSchema(Schema):
#     regex = fields.List(fields.Dict)
#     # workaround = fields.Str()
#     # solution = fields.Str()


# class OutputSchema(Schema):
#     conversation_id = fields.Str()
#     message_id = fields.Str()
#     source = fields.Str()
#     dryrun = fields.Str()
#     debug = fields.Str()
#     intention = fields.Nested(IntentionSchema())
#     user_response = fields.Nested(PapyrusSchema)
    

# app = Flask(__name__)


# def make_request_call(url, headers, payload, method='POST'):
#     json_payload = json.dumps(payload)

#     if method == 'POST':
#         response = requests.post(url, headers=headers, data=json_payload)
#     else:
#         raise NotImplementedError

#     if response.status_code == 200:
#         print('Request successful!')
#         print(response.json())
#     else:
#         print('Request failed!')
#         print(response.text) 
            
#     return response


# def run_topic_module(user_input=None):
#     # Set up the URL
#     url = 'http://ip-10-0-0-89.us-west-2.compute.internal:8888/dev'

#     # Set up the headers
#     headers = {
#         'Content-Type': 'application/json',
#         'X-Api-Key': '230e2b5e-fb08-405c-b9d2-f17e66be3b47'
#     }

#     # Set up the request body
#     payload = {
#         'user_input': user_input
#     }
#     response = make_request_call(url, headers, payload)
#     return response

        
# def run_intention_module(topic_output):
#     # Set up the URL
#     url = 'http://ip-10-0-0-89.us-west-2.compute.internal:8089/query'

#     # Set up the headers
#     headers = {
#         'Content-Type': 'application/json',
#     }

#     # Set up the request body
#     payload = {
#         # 'question': topic_output['user_input_desc']['user_input']
#         'question': topic_output['user_input_desc']
#     }
#     response = make_request_call(url, headers, payload)
#     return response


# def run_papyrus_module(topic_output, intention_output):
#     # Set up the URL
#     url = 'http://ip-10-0-0-89.us-west-2.compute.internal:8090/generate'
#     # url = 'http://localhost:3333/generate'

#     # Set up the headers
#     headers = {
#         'Content-Type': 'application/json',
#     }
#     # Set up the request body
#     payload = {
#         'user_input_desc': topic_output['user_input_desc'],
#         'page_content': '' # intention_output['page_content']
#         # 'page_content': intention_output['page_content']
#     }
#     response = make_request_call(url, headers, payload)
#     return response    


# @app.route('/papyrusGen', methods=['POST'])
# def testPipeline():
#     """
#     """
#     timer_start = time.time()

#     run_topic = True
#     run_bice = False 
#     run_papyrus = True 
    
    
#     ## =======================================================
#     ## Input parsing
#     ## =======================================================
#     # parse params 
#     params = request.args.to_dict()
#     params = {str(k).strip('\\'): str(v).strip('\\') for k, v in params.items()}
#     conversation_id = params.get('conversation_id', 'placeholder_conv_id')
#     message_id = params.get('message_id', 'placeholder_message_id')
#     source = params.get('source', 'placeholder_source')
#     dryrun = params.get('dryrun', 'placeholder_dryrun')
#     debug = params.get('debug', 'placeholder_debug')
    
#     # parse body
#     raw_query = request.get_json(force=True)
#     user_input_body = raw_query.get('user_input', '')
#     nodes_run_data_body = raw_query.get('nodes_run_data', [])

#     ## =======================================================
#     ## Topic module 
#     ## =======================================================
#     if run_topic:
#         topic_output = run_topic_module(user_input=user_input_body)
#         time_topic_module = time.time()-timer_start
#         print(f"topic module takes {time_topic_module}")
#         # topic_output = topic_output['message']
#         print(f'topic_output.text: {topic_output.text}')
#         topic_output_message = json.loads(topic_output.text).get('message')
#         try:
#             # double json.loads....
#             topic_output_json = json.loads(json.loads(topic_output_message))   # json output
#         except Exception as errmsg:
#             print(f'!!! ERRROR in topic_output !!! {errmsg}')
#             raise 
    
#         # formatting the topic module output
#         topic_output_json['user_input_desc'] = topic_output_json[
#             'user_input_desc'].replace('\nUSER:', '').replace('USER: ', '')

#         def try_convert_to_list(key):
#             if not isinstance(topic_output_json[key], list):
#                 try:
#                     key_list = ast.literal_eval(topic_output_json[key])
#                     if not isinstance(key_list, list):
#                         import pdb; pdb.set_trace()
#                 except:
#                     key_list = [topic_output_json[key]]
#                     import pdb; pdb.set_trace()
#             else:
#                 key_list = topic_output_json[key] 
                
#                 # the topic_output_json[key] is Dict ..
#                 if isinstance(key_list, dict):
#                     key_list = [f'{k}. {v}' for k, v in key_list.items()]
                
#             return key_list       
            
#         steps_list = try_convert_to_list('steps')
#         solutions_list = try_convert_to_list('solutions')
#         extracted_entity_list = try_convert_to_list('extracted_entity')
                        
#         agg_intention = {
#             'goal': f"{topic_output_json.get('goal')}\n" if topic_output_json.get('goal') else '',
#             'main_question': f"{topic_output_json.get('main_question')}" if topic_output_json.get('main_question') else '',
#             'major_problem': f"{topic_output_json.get('major_problem')}" if topic_output_json.get('major_problem') else '',
#             'situation': f"{topic_output_json.get('situation')}" if topic_output_json.get('situation') else '',
#             'summary': f"{topic_output_json.get('summary')}" if topic_output_json.get('summary') else '',
#             'extracted_entity': extracted_entity_list if extracted_entity_list else [],
#             'system_message': f"'{topic_output_json.get('system_message')}" if topic_output_json.get('system_message') else [],
#             'steps': steps_list if steps_list else [],
#             'solutions': solutions_list if solutions_list else [],
#         }    
#         # extracted_entity
#         # aggregated version    
#         # topic_output_json['intention'] = ''.join([value for _, value in agg_intention.items()])
#         # topic_output_json['intention'] = agg_intention
#         myIntention = dict(
#             goal=agg_intention['goal'],
#             main_question=agg_intention['main_question'],
#             major_problem=agg_intention['major_problem'],
#             situation=agg_intention['situation'],
#             summary=agg_intention['summary'],
#             extracted_entity=agg_intention['extracted_entity'],
#             system_message=agg_intention['system_message'],
#             steps=agg_intention['steps'],
#             solutions=agg_intention['solutions']
#             )
#     else:
#         time_topic_module = time.time()-timer_start
#         myIntention = dict(
#             goal='myGoal', 
#             main_question='myMainQuestion', 
#             major_problem='myMajorProblem', 
#             situation='mySituation', 
#             summary='mySummary', 
#             extracted_entity=['ext_ent'], 
#             system_message=['sys_msg'],
#             steps=['step1', 'step2', 'step3'], 
#             solutions=['solution1', 'solution2', 'solution3']
#             )

    
#     ## =======================================================
#     ## BI/CE module -- commented
#     ## =======================================================
#     if run_bice:
#         # intention_output = run_intention_module(topic_output)
#         # intention_output = run_intention_module(topic_output_json)     # json input
#         time_intention_module = time.time()-timer_start-time_topic_module
#         print(f"intention module takes {time_intention_module}")
#         # intention_output = json.loads(intention_output.text)['message'][0]
#     else:
#         time_intention_module = time.time()-timer_start-time_topic_module
#         intention_output = ''
    
#     ## =======================================================
#     ## Papyrus module 
#     ## =======================================================
#     if run_papyrus:
        
#         # input handling for March demo. `\\`
#         has_use_case_1_device = topic_output_json['user_input_desc'].find('dtw-302-9300-sw-1') >= 0
#         has_use_case_1_sentence = topic_output_json['user_input_desc'].find('never establishes') >= 0
#         has_backslashes = topic_output_json['user_input_desc'].find('\\') >= 0
        
#         if has_use_case_1_device and has_use_case_1_sentence and not has_backslashes:
#             use_case_1_body_splitted = topic_output_json['user_input_desc'].split('never establishes.')
#             use_case_1_body = use_case_1_body_splitted[0] + '\\ never establishes.' + use_case_1_body_splitted[1]
#             test_against = "One of our network management systems has shown that memory utilization for a cat9200 switched named dtw-302-9300-sw-1 has been increasing. The device is attempting to send telemetry data to DNAC but the connection \\ never establishes. I have noticed that the pubd process is consuming the majority of memory. The device is trying to send telemetry data to our DNAC, but it seems the receiver is responding with a device not found.  Is this a bug?"
#             # assert test_against == use_case_1_body
#             topic_output_json['user_input_desc'] = use_case_1_body
            
#         # papyrus_output = run_papyrus_module(topic_output, intention_output)
#         papyrus_output = run_papyrus_module(topic_output_json, intention_output)
#         time_papyrus_module = time.time()-timer_start-time_topic_module-time_intention_module
#         print(f"papyrus module takes {time_papyrus_module}")
#         print(json.loads(papyrus_output.text)['message'])
#         user_response = json.dumps(json.loads(papyrus_output.text)['message'])
        
#         # user_response parsing 
#         # use case 1: device memory issue 
#         try:
#             user_response = json.loads(user_response)
#         except:
#             import pdb; pdb.set_trace()
            
#         try:
#             user_response = user_response['regex']
#         except:
#             import pdb; pdb.set_trace()        
        
#         user_response_list = papyrus_output_formatting(topic_output_json, user_response)
        
#         MyUserResponse = dict(
#             regex = user_response_list #,
#             # workaround = 'myWorkaround',
#             # solution = 'mySolution'
#             )
#     else:
#         user_response_list = [{'regex': 'No Papyrus module run', 'signature': 'No Papyrus module run'}]
#         MyUserResponse = dict(
#             regex = user_response_list #,
#             # workaround = 'myWorkaround',
#             # solution = 'mySolution'
#             )
        

#     # the output format
#     ## =======================================================
#     ## Output formatting
#     ## =======================================================
    
#     try:
#         if str(debug) == 'True':
#             # pipeline_output = {
#             #     "conversation_id": conversation_id,     # pass through
#             #     "message_id": message_id,               # pass through 
#             #     "user_response": user_response,
#             #     # "user_response": json.loads(papyrus_output.text)['message'], 
#             #     "nodes_run_cmds": {},                                          # empty,
#             #     "intention": intention,  # jsonify 
#             #     # "intention": topic_output_json.get('intention', '')
#             #     # "intention": json.dumps(intention),  # jsonify
#             #     "[DEBUG] source": source,
#             #     "[DEBUG] dryrun": str(dryrun),
#             #     "[DEBUG] debug": str(debug),
#             #     "[DEBUG] user_input": user_input_body,
#             #     "[DEBUG] nodes_run_data": nodes_run_data_body,
#             # }
#             output = dict(
#                 conversation_id=conversation_id, 
#                 message_id=message_id, 
#                 source=str(source),
#                 dryrun=str(dryrun),
#                 debug=str(debug),
#                 intention=myIntention, 
#                 user_response=MyUserResponse)
            
#         else:
#             # pipeline_output = {
#             #     "conversation_id": conversation_id,     # pass through
#             #     "message_id": message_id,               # pass through 
#             #     "user_response": user_response,
#             #     # "user_response": json.loads(papyrus_output.text)['message'], 
#             #     "intention": intention,  # jsonify
#             #     # "intention": jsonify(topic_output_json.get('intention', '')),  # jsonify
#             #     # "intention": json.dumps(intention),  # jsonify
#             #     "nodes_run_cmds": {}                                          # empty
#             # }
#             output = dict(
#                 conversation_id=conversation_id, 
#                 message_id=message_id, 
#                 intention=myIntention, 
#                 user_response=MyUserResponse)
                
#         # output = dict(
#         #     conversation_id='myConv', 
#         #     message_id='myMSG', 
#         #     intention=myIntention, 
#         #     user_response=MyUserResponse)

#         schema = OutputSchema()
#         result = schema.dump(output)

#         # import pdb; pdb.set_trace()
#         return jsonify(result), 200
        
#         # print(f'pipeline_output.keys(): {pipeline_output.keys()}')
#         # if len(pipeline_output.keys()) > 1:
#         #     pipeline_output['intention']
#         #     print(f'pipeline_output.keys(): {pipeline_output.keys()}')
#         # import pdb; pdb.set_trace()
#         # return jsonify(pipeline_output), 200
#         # return json.loads(pipeline_output), 200
#     except:
#         error_body = {'message': 'error....'}
#         # import pdb; pdb.set_trace()
#         return jsonify(error_body), 422
#         return error_body, 422
    


# @app.route('/health', methods=['GET'])
# def health():
#     resp = jsonify({"message": json.dumps('[PapyrusRelease] Hello! Up and running. ', default=vars)})
#     resp.status_code = 200
#     return resp 


# def papyrus_output_formatting(topic_output_json, user_response):
#     has_use_case_1_device = topic_output_json['user_input_desc'].find('dtw-302-9300-sw-1') >= 0
#     has_use_case_1_sentence = topic_output_json['user_input_desc'].find('never establishes') >= 0
#     has_user_case_2_sentence = topic_output_json['user_input_desc'].upper().find('PSIRT') >= 0
#     if has_use_case_1_device and has_use_case_1_sentence:
#         user_response_list = []
#         # import pdb;pdb.set_trace()
#         try:
#             cmd_split = user_response.split('Command:')
#             cmd_split = [f'{item}' for item in cmd_split if item != '']
#         except:
#             import pdb; pdb.set_trace()
        
#         if not cmd_split:
#             raise Exception('cmd_split empty!')

#         # import pdb; pdb.set_trace()
#         try:
#             for each_line in cmd_split:
#                 sig_split = each_line.split('Signature:')
#                 command_clean = sig_split[0]
#                 signature_clean = sig_split[1]
#                 # if len(sig_split[0]) > 0 and sig_split[0].startswith(':'):
#                 command_clean = sig_split[0].replace(':', '').replace(',', '').strip(' ')
#                 if len(sig_split[1]) > 0:
#                     signature_clean = sig_split[1].strip(' ')
#                 if len(command_clean) > 0 and len(signature_clean) > 0:
#                     user_response_list.append({'command': command_clean, 'signature': signature_clean})
#             return user_response_list
#         except:
#             import pdb; pdb.set_trace()
    
#     # use case 2: psirt                
#     elif has_user_case_2_sentence:
#         try:
#             pass 
#         except:
#             pass 
#     else:
#         pass 


    
# if __name__ == "__main__":
#     # testPipeline()
#     app.run(debug=True, host='0.0.0.0', port=2222)
