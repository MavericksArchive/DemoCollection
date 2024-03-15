"""
after emily feedback on 03/11/2024
"""
import ast 
import json
import time

import requests
from flask import Flask, request, jsonify


from output_schema import OutputSchema
    

app = Flask(__name__)


def make_request_call(url, headers, payload, method='POST'):
    json_payload = json.dumps(payload)

    # import pdb; pdb.set_trace()
    
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


def run_topic_module(user_input=None, myIntentionFull=False):
    # Set up the URL
    url = 'http://ip-10-0-0-89.us-west-2.compute.internal:8888/dev'
    # url = 'http://ip-10-0-0-93.us-west-2.compute.internal:8888/dev'
    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': '230e2b5e-fb08-405c-b9d2-f17e66be3b47',
    }
    payload = {'user_input': user_input, 'myIntentionFull': str(myIntentionFull)}
    response = make_request_call(url, headers, payload)
    return response

        
def run_intention_module(topic_output):
    # Set up the URL
    url = 'http://ip-10-0-0-89.us-west-2.compute.internal:8089/query'
    # url = 'http://ip-10-0-0-93.us-west-2.compute.internal:8089/query'
    headers = {'Content-Type': 'application/json'}
    payload = {
        # 'question': topic_output['user_input_desc']['user_input']
        'question': topic_output['user_input_desc']
    }
    response = make_request_call(url, headers, payload)
    return response


def run_papyrus_module(topic_output, run_papyrus_solution: bool, intention_output=None):
    """
    :param topic_output:
    :param intention_output:
    :param run_papyrus_solution:
    :return response: 
    """
    # Set up the URL
    url = 'http://ip-10-0-0-89.us-west-2.compute.internal:8090/generate'
    # url = 'http://ip-10-0-0-93.us-west-2.compute.internal:8090/generate'
    headers = {'Content-Type': 'application/json'}
    payload = {
        'user_input_desc': topic_output['user_input_desc'],
        'page_content': '', # intention_output['page_content'],
        'run_papyrus_solution': run_papyrus_solution
    }
    response = make_request_call(url, headers, payload)
    return response    


@app.route('/papyrusGen', methods=['POST'])
def testPipeline():
    """
    """
    timer_start = time.time()

    run_topic = False
    run_bice = False 
    run_papyrus = True 
    
    ## ======================  Input parsing  ==============================
    # parse params 
    params = request.args.to_dict()
    params = {str(k).strip('\\'): str(v).strip('\\') for k, v in params.items()}
    conversation_id = params.get('conversation_id', 'placeholder_conv_id')
    message_id = params.get('message_id', 'placeholder_message_id')
    source = params.get('source', 'placeholder_source')
    dryrun = params.get('dryrun', 'placeholder_dryrun')
    debug = params.get('debug', 'placeholder_debug')
    # run_papyrus_solution = params.get('run_papyrus_solution', True)
    
    # if run_papyrus_solution == 'True':
    #     run_papyrus_solution = True  
    # elif run_papyrus_solution == 'False':
    #     run_papyrus_solution = False
    # else:
    #     raise Exception('run_papyrus_solution is either True or False')
    
    # parse body
    raw_query = request.get_json(force=True)
    user_input_body = raw_query.get('user_input', '')
    nodes_run_data_body = raw_query.get('nodes_run_data', [])

    ## ======================  Topic module  ==============================    
    myIntentionFull = False
    if run_topic:        
        topic_output = run_topic_module(user_input=user_input_body, myIntentionFull=myIntentionFull)
        time_topic_module = time.time() - timer_start
        print(f"topic module takes {time_topic_module}")
        # topic_output = topic_output['message']
        print(f'topic_output.text: {topic_output.text}')
        topic_output_message = json.loads(topic_output.text).get('message')
        try:
            # double json.loads....
            topic_output_json = json.loads(json.loads(topic_output_message))   # json output
        except Exception as errmsg:
            print(f'!!! ERRROR in topic_output !!! {errmsg}')
            raise 
    
        # formatting the topic module output
        topic_output_json['user_input_desc'] = topic_output_json[
            'user_input_desc'].replace('\nUSER:', '').replace('USER: ', '')

        def _try_convert_to_list(key):
            if not isinstance(topic_output_json[key], list):
                try:
                    key_list = ast.literal_eval(topic_output_json[key])
                    if not isinstance(key_list, list):
                        import pdb; pdb.set_trace()
                except:
                    key_list = [topic_output_json[key]]
                    import pdb; pdb.set_trace()
            else:
                key_list = topic_output_json[key] 
                
                # the topic_output_json[key] is Dict ..
                if isinstance(key_list, dict):
                    key_list = [f'{k}. {v}' for k, v in key_list.items()]
                
            return key_list       
            
        steps_list = _try_convert_to_list('steps')
        extracted_entity_list = _try_convert_to_list('extracted_entity')
        if myIntentionFull:       
            solutions_list = _try_convert_to_list('solutions')
        
        if myIntentionFull:     
            agg_intention = {
                'goal': f"{topic_output_json.get('goal')}\n" if topic_output_json.get('goal') else '',
                'main_question': f"{topic_output_json.get('main_question')}" if topic_output_json.get('main_question') else '',
                'major_problem': f"{topic_output_json.get('major_problem')}" if topic_output_json.get('major_problem') else '',
                'situation': f"{topic_output_json.get('situation')}" if topic_output_json.get('situation') else '',
                'summary': f"{topic_output_json.get('summary')}" if topic_output_json.get('summary') else '',
                'extracted_entity': extracted_entity_list if extracted_entity_list else [],
                'system_message': f"'{topic_output_json.get('system_message')}" if topic_output_json.get('system_message') else [],
                'steps': steps_list if steps_list else [],
                'solutions': solutions_list if solutions_list else []}    
            myIntention = dict(
                goal=agg_intention['goal'],
                main_question=agg_intention['main_question'],
                major_problem=agg_intention['major_problem'],
                situation=agg_intention['situation'],
                summary=agg_intention['summary'],
                extracted_entity=agg_intention['extracted_entity'],
                system_message=agg_intention['system_message'],
                steps=agg_intention['steps'],
                solutions=agg_intention['solutions'])
            
        else:
            agg_intention = {
                'extracted_entity': extracted_entity_list if extracted_entity_list else [],
                'system_message': f"'{topic_output_json.get('system_message')}" if topic_output_json.get('system_message') else [],
                'steps': steps_list if steps_list else []}    
            myIntention = dict(
                extracted_entity=agg_intention['extracted_entity'],
                system_message=agg_intention['system_message'],
                steps=agg_intention['steps'])
        
        # topic_output_json['intention'] = ''.join([value for _, value in agg_intention.items()])
        # topic_output_json['intention'] = agg_intention
            
    else:     # not running topic module...
        # time.sleep(3)
        if myIntentionFull:
            time_topic_module = time.time()-timer_start
            myIntention = dict(
                goal='myGoal', 
                main_question='myMainQuestion', 
                major_problem='myMajorProblem', 
                situation='mySituation', 
                summary='mySummary', 
                extracted_entity=['ext_ent'], 
                system_message=['sys_msg'],
                steps=['step1', 'step2', 'step3'], 
                solutions=['solution1', 'solution2', 'solution3'])
        else:
            time_topic_module = time.time()-timer_start            
            # workflow 1
            has_use_case_1_device = user_input_body.find('MRE-Edge2.cisco.com') >= 0
            has_use_case_1_sentence = user_input_body.find('never establishes') >= 0
            has_backslashes = user_input_body.find('\\') >= 0
            if has_use_case_1_device and has_use_case_1_sentence:
                json_result = {"extracted_entity": ["cat9200 switch", "MRE-Edge2.cisco.com", "DNAC"],
                            "steps": ["Analyze affected devices using our Papyrus model or the below code.", 
                                        "Suggest possible remediation actions.", 
                                        "Suggest the user integrate the remediation action into their change management process, such as creating a ServiceNow incident ticket."]}            

                myIntention = dict(
                    extracted_entity=json_result['extracted_entity'], 
                    system_message=[],
                    steps=json_result['steps'])
                topic_output_json = {'user_input_desc': user_input_body}
                

            # workflow 7
            has_use_case_2_psirt = user_input_body.find('PSIRT') >= 0
            has_use_case_2_sentence = user_input_body.find('cisco-sa-iosxe-webui-privesc-j22SaA4z') >= 0
            if has_use_case_2_psirt and has_use_case_2_sentence:
                json_result = {"extracted_entity": ["PSIRT cisco-sa-iosxe-webui-privesc-j22SaA4z"],
                            "steps": ["Analyze affected devices using our Papyrus model or the below code.", 
                                    "Suggest possible remediation actions.", 
                                    "Suggest the user integrate the remediation action into their change management process, such as creating a ServiceNow incident ticket."]}

                myIntention = dict(
                    extracted_entity=json_result['extracted_entity'], 
                    system_message=[],
                    steps=json_result['steps'])
                topic_output_json = {'user_input_desc': user_input_body}

            topic_output_json = {'user_input_desc': user_input_body}


    ## ======================  BI/CE module  ==============================    
    if run_bice:
        # intention_output = run_intention_module(topic_output)
        # intention_output = run_intention_module(topic_output_json)     # json input
        time_intention_module = time.time()-timer_start-time_topic_module
        print(f"intention module takes {time_intention_module}")
        # intention_output = json.loads(intention_output.text)['message'][0]
    else:
        time_intention_module = time.time()-timer_start-time_topic_module
        intention_output = ''
    
    ## ======================  Papyrus module  ==============================    
    if run_papyrus:
        
        run_papyrus_solution = True
        
        # input handling for March demo. `\\`
        has_use_case_1_device = user_input_body.find('MRE-Edge2.cisco.com') >= 0
        has_use_case_1_sentence = user_input_body.find('never establishes') >= 0
        has_backslashes = user_input_body.find('\\') >= 0
        
        if has_use_case_1_device and has_use_case_1_sentence and not has_backslashes:
            use_case_1_body_splitted = user_input_body.split('never establishes.')
            use_case_1_body = use_case_1_body_splitted[0] + '\\ never establishes.' + use_case_1_body_splitted[1]
            # test_against = "One of our network management systems has shown that memory utilization for a cat9200 switched named MRE-Edge2.cisco.com has been increasing. The device is attempting to send telemetry data to DNAC but the connection \\ never establishes. I have noticed that the pubd process is consuming the majority of memory. The device is trying to send telemetry data to our DNAC, but it seems the receiver is responding with a device not found.  Is this a bug?"
            # assert test_against == use_case_1_body
            user_input_body = use_case_1_body
        
        # print(f'[DEBUG]topic_output_json : {topic_output_json}')
        # print(f'[DEBUG]intention_output : {intention_output}')
        # print(f'[DEBUG]run_papyrus_solution : {run_papyrus_solution}')
        topic_output_json['user_input_desc'] = user_input_body
        
        papyrus_output = run_papyrus_module(
            topic_output_json, run_papyrus_solution, intention_output=intention_output)
        time_papyrus_module = time.time()-timer_start-time_topic_module-time_intention_module
        print(f"papyrus module takes {time_papyrus_module}")
        print(json.loads(papyrus_output.text)['message'])
        user_response = json.dumps(json.loads(papyrus_output.text)['message'])
        
        # user_response parsing  
        try:
            user_response = json.loads(user_response)
            user_response_regex = user_response['regex']
            if run_papyrus_solution:
                user_response_solution = user_response['solution']
        except:
            import pdb; pdb.set_trace()
        
        try:
            user_response_regex_list = papyrus_output_regex_formatting(user_input_body, user_response_regex)
        except:
            user_response_regex_list = [user_response_regex]
        
        if run_papyrus_solution:
            try:
                user_response_solution_list = papyrus_output_solution_formatting(user_input_body, user_response_solution)
            except:
                user_response_solution_list = [user_response_solution]        
        
        
        # print(f'stopping for dev/test papyrus solution')
        # import pdb; pdb.set_trace()
        
        
        if run_papyrus_solution:
            MyUserResponse = dict(
                regex = user_response_regex_list,
                solutions = user_response_solution_list
                )
        else:
            MyUserResponse = dict(
                regex = user_response_regex_list,
                )
    else:
        user_response_regex_list = [
            {'regex': 'No Papyrus module run', 
             'signature': 'No Papyrus module run'}]
        if run_papyrus_solution:
            MyUserResponse = dict(
                regex = user_response_regex_list,
                solutions = ['mySolution'])
        else:
            MyUserResponse = dict(regex = user_response_regex_list)
    myIntention=dict(
        solutions=user_response_solution_list
    )
        

    ## ======================  Output formatting  ==============================  
    try:
        if str(debug) == 'True':
            output = dict(
                conversation_id=conversation_id, 
                message_id=message_id, 
                source=str(source),
                dryrun=str(dryrun),
                debug=str(debug),
                intention=myIntention, 
                user_response=MyUserResponse)
            
        else:
            output = dict(
                conversation_id=conversation_id, 
                message_id=message_id, 
                intention=myIntention, 
                user_response=MyUserResponse)
                
        schema = OutputSchema()
        result = schema.dump(output)
        return jsonify(result), 200
        
    except:
        error_body = {'message': 'error....'}
        return jsonify(error_body), 422
    


@app.route('/health', methods=['GET'])
def health():
    resp = jsonify({"message": json.dumps('[PapyrusRelease] Hello! Up and running. ', default=vars)})
    resp.status_code = 200
    return resp 


def papyrus_output_regex_formatting(topic_output_json, user_response, key_pair = ['Command', 'Signature']):
    import re
    """ Here assume the first component in key_pair is the start word, 
       and the second component in key_pair is the end word.
    """
    user_response_list = []

    total_counts = 0
    for sub in key_pair:  
        total_counts += len([i for i in range(len(user_response)) if user_response.startswith(sub, i)])

    if total_counts > 0:
       
       split_command=re.split(r'\bCommand\b:?', user_response)
           
       for sub in split_command:
            if 'Signature' in sub:
                segments = re.split(r'\bSignature\b:?', sub)
                
                cmd_clean = segments[0].replace(',', '').strip(' ').rstrip('\n')
                seg_1_clean = segments[1].replace(',', '').strip(' ').rstrip('\n')
                
                if cmd_clean == " show" or cmd_clean == "show":
                    import pdb; pdb.set_trace()                
                
                user_response_list.append({'Command': cmd_clean, 'Signature': seg_1_clean})
                user_response_list.extend([{'Command': '', 'Signature': t_} for t_ in segments[2:]])


                # user_response_list.append({'Command': segments[0], 'Signature': segments[1]})
                # user_response_list.extend([{'Command': '', 'Signature': t_} for t_ in segments[2:]])
            elif len(sub): 
                user_response_list.append({'Command': sub})
    else:
        user_response_list.append({'raw_summary': user_response})    


    return user_response_list



def papyrus_output_solution_formatting(user_input_body, user_response_solution):
    """
    TODO: split if needed? instead of wrapping it as a list?
    TODO: this is for the demo only... need to generalize.
    """
    has_use_case_1_device = user_input_body.find('MRE-Edge2.cisco.com') >= 0
    has_use_case_1_sentence = user_input_body.find('never establishes') >= 0
    
    has_use_case_2_psirt = user_input_body.find('PSIRT') >= 0
    has_use_case_2_sentence = user_input_body.find('cisco-sa-iosxe-webui-privesc-j22SaA4z') >= 0

    try:
        if has_use_case_1_device and has_use_case_1_sentence:
            user_response_solution_list = [sentence.strip() for sentence in user_response_solution.split('.')]
            final_list = []
            
            # servicenow = 'Open a ticket for an emergency reload.'
            servicenow = None
            if servicenow:
                sent1 = f"{user_response_solution_list[0]}. {user_response_solution_list[1]}. {servicenow}"
            else:
                sent1 = f"{user_response_solution_list[0]}. {user_response_solution_list[1]}."
            sent2 = f"{user_response_solution_list[2]}.".rstrip('.') + '.'
            # note = '. '.join(user_response_solution_list[3:]).rstrip('/').rstrip('.') + '.'
            note = ''
            if note != '':
                note = note.rstrip('.') + '.'
                final_list = [sent1, sent2, note]
            else:
                final_list = [sent1, sent2]
            
            
        if has_use_case_2_psirt and has_use_case_2_sentence:
            final_list = []
            user_response_solution_list = [sentence.strip() for sentence in user_response_solution.split('later')]
            sent1 = f"{user_response_solution_list[0]} later."
            sent2_note_list = [sentence.strip() for sentence in user_response_solution_list[1].split('.') if sentence != '']
            sent2 = f"{sent2_note_list[0]}. {sent2_note_list[1]}".rstrip('.') + '.'
            note = '. '.join(sent2_note_list[2:]).rstrip('/')
            if note != '':
                note = note.rstrip('.') + '.'
                final_list = [sent1, f"{sent2} {note}"]
            else:
                final_list = [sent1, sent2]
        
        return final_list
    except:
        return [user_response_solution]



    
if __name__ == "__main__":
    # testPipeline()
    app.run(debug=True, host='0.0.0.0', port=2222)
