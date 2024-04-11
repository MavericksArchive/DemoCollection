"""
The main thread docker. 
"""
import re
import ast 
import json
import time

import requests
from flask import Flask, request, jsonify


from output_schema import OutputSchema
    

app = Flask(__name__)


def make_request_call(url, headers, payload, method='POST'):
    """
    :param url:
    :param headers:
    :param payload:
    :param method:
    :return response: 
    """
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


def run_intention_module(user_input: str = None, my_intention_full: bool = False, dev_server: bool = True):
    """
    :param user_input:
    :param my_intention_full:
    :return response:
    """
    # Set up the URL    
    if dev_server:
        # (a) dev server
        url = 'http://ip-10-0-0-89.us-west-2.compute.internal:8888/dev'
    else:
        # (b) dedicated server 
        url = 'http://ip-10-0-0-93.us-west-2.compute.internal:8888/dev'
    
    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': '230e2b5e-fb08-405c-b9d2-f17e66be3b47',
    }
    payload = {'user_input': user_input, 'my_intention_full': str(my_intention_full)}
    response = make_request_call(url, headers, payload)
    return response

        
def run_bi_ce_module(topic_output, dev_server: bool = True):
    """
    :param topic_output:
    :return response:
    """
    # Set up the URL
    if dev_server:
        # (a) dev server
        url = 'http://ip-10-0-0-89.us-west-2.compute.internal:8089/query'
    else:    
        # (b) dedicated server 
        url = 'http://ip-10-0-0-93.us-west-2.compute.internal:8089/query'
            
    headers = {'Content-Type': 'application/json'}
    payload = {
        # 'question': topic_output['user_input_desc']['user_input']
        'question': topic_output['user_input_desc']
    }
    response = make_request_call(url, headers, payload)
    return response


def run_papyrus_module(topic_output, run_papyrus_solution: bool, bi_ce_output=None, dev_server: bool = True):
    """
    :param topic_output:
    :param run_papyrus_solution:
    :param bi_ce_output: intention module output. Not used.
    :return response: 
    """
    # Set up the URL
    if dev_server:
        # (a) dev server
        url = 'http://ip-10-0-0-89.us-west-2.compute.internal:8090/generate'
    else:
        # (b) dedicated server 
        url = 'http://ip-10-0-0-93.us-west-2.compute.internal:8090/generate'
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        'user_input_desc': topic_output['user_input_desc'],
        'page_content': '', # bi_ce_output['page_content'],  # not used
        'run_papyrus_solution': run_papyrus_solution
    }
    response = make_request_call(url, headers, payload)
    return response    



@app.route('/papyrusGen', methods=['POST'])
def testPipeline():
    """The endpoint"""
    timer_start = time.time()

    # flexible control on the modules for demo purpose
    run_intention = False
    run_bice = False 
    run_papyrus = True 
    
    ## ======================  Input parsing  ==============================
    # parse params 
    params = request.args.to_dict()
    
    # if params are empty json 
    params = {str(k).strip('\\'): str(v).strip('\\') for k, v in params.items()}

    conversation_id = params.get('conversation_id', 'placeholder_conv_id')
    message_id = params.get('message_id', 'placeholder_message_id')
    source = params.get('source', 'placeholder_source')
    dryrun = params.get('dryrun', 'placeholder_dryrun')
    debug = params.get('debug', 'placeholder_debug')
    # run_papyrus_solution = params.get('run_papyrus_solution', True)
        
    # parse body
    raw_query = request.get_json(force=True)
    user_input_body = raw_query.get('user_input', '')
    nodes_run_data_body = raw_query.get('nodes_run_data', [])  # not used

    ## Set default to bypass in the demo
    ## ======================  Intention module  ==============================    
    my_intention_full = False
    if run_intention:        
        topic_output = run_intention_module(user_input=user_input_body, my_intention_full=my_intention_full)
        
        print(f'topic_output.text: {topic_output.text}')
        topic_output_message = json.loads(topic_output.text).get('message')
        try:
            # double json.loads....
            topic_output_json = json.loads(json.loads(topic_output_message))   # json output
        except Exception as errmsg:
            print(f'!!! ERROR in topic_output !!! {errmsg}')
            raise 
    
        # Formatting the topic module output
        topic_output_json['user_input_desc'] = topic_output_json[
            'user_input_desc'].replace('\nUSER:', '').replace('USER: ', '')
    
        # Formatting the topic module output. Try the output to convert to a list            
        steps_list = _try_convert_to_list(topic_output_json, 'steps')
        extracted_entity_list = _try_convert_to_list(topic_output_json, 'extracted_entity')
        
        if my_intention_full:       
            solutions_list = _try_convert_to_list(topic_output_json, 'solutions')
        
        if my_intention_full:     
            my_intention = dict(
                goal=f"{topic_output_json.get('goal')}\n" if topic_output_json.get('goal') else '',
                main_question=f"{topic_output_json.get('main_question')}" if topic_output_json.get('main_question') else '',
                major_problem=f"{topic_output_json.get('major_problem')}" if topic_output_json.get('major_problem') else '',
                situation=f"{topic_output_json.get('situation')}" if topic_output_json.get('situation') else '',
                summary=f"{topic_output_json.get('summary')}" if topic_output_json.get('summary') else '',
                extracted_entity=extracted_entity_list if extracted_entity_list else [],
                system_message=f"'{topic_output_json.get('system_message')}" if topic_output_json.get('system_message') else [],
                steps=steps_list if steps_list else [],
                solutions=solutions_list if solutions_list else [])
        else:
            my_intention = dict(
                extracted_entity=extracted_entity_list if extracted_entity_list else [],
                system_message=f"'{topic_output_json.get('system_message')}" if topic_output_json.get('system_message') else [],
                steps=steps_list if steps_list else [])      
        
        time_intention_module = time.time() - timer_start
        print(f"topic module takes {time_intention_module}")           
    else:     
        # not running topic module...
        # time.sleep(3)
        if my_intention_full:
            my_intention = dict(
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
            topic_output_json = {'user_input_desc': user_input_body}
        time_intention_module = time.time() - timer_start
    
    ## Set default to bypass in the demo
    ## ======================  BI/CE module  ==============================   
    if run_bice:
        # bi_ce_output = run_bi_ce_module(topic_output)
        bi_ce_output = run_bi_ce_module(topic_output_json)                     # json input
        bi_ce_output = json.loads(bi_ce_output.text)['message'][0]
        time_bi_ce_module = time.time() - timer_start - time_intention_module  
        print(f"bi/ce module takes {time_bi_ce_module}")
    else:
        bi_ce_output = ''      # not used               
        time_bi_ce_module = time.time() - timer_start - time_intention_module   
    
    ## ======================  Papyrus module  ==============================    
    if run_papyrus:

        # generate the solution at the same time
        run_papyrus_solution = True
        
        user_input_body = demo_use_case_prompt_edit(user_input_body)        
        # print(f'[DEBUG]topic_output_json : {topic_output_json}')
        # print(f'[DEBUG]bi_ce_output : {bi_ce_output}')
        # print(f'[DEBUG]run_papyrus_solution : {run_papyrus_solution}')
        topic_output_json['user_input_desc'] = user_input_body
        
        papyrus_output = run_papyrus_module(
            topic_output_json, run_papyrus_solution, bi_ce_output=bi_ce_output)
        
        print(json.loads(papyrus_output.text)['message'])
        user_response = json.dumps(json.loads(papyrus_output.text)['message'])
        
        # user_response parsing  
        user_response = json.loads(user_response)
        user_response_regex = user_response['regex']
        if run_papyrus_solution:
            user_response_solution = user_response['solution']
        
        try:
            user_response_regex_list = papyrus_output_regex_formatting(user_input_body, user_response_regex)
        except:
            user_response_regex_list = [user_response_regex]
        
        if run_papyrus_solution:
            try:
                user_response_solution_list = papyrus_output_solution_formatting(user_input_body, user_response_solution)
            except:
                user_response_solution_list = [user_response_solution]        
                
        if run_papyrus_solution:
            MyUserResponse = dict(
                regex = user_response_regex_list,
                solutions = user_response_solution_list
                )
        else:
            MyUserResponse = dict(
                regex = user_response_regex_list,
                )
        
        time_papyrus_module = time.time() - timer_start - time_intention_module - time_intention_module
        print(f"papyrus module takes {time_papyrus_module}")
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
    
    # Patchwork to comply with what the UI expects. 
    # solution is beneath the intention.
    my_intention=dict(
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
                intention=my_intention, 
                user_response=MyUserResponse)
        else:
            output = dict(
                conversation_id=conversation_id, 
                message_id=message_id, 
                intention=my_intention, 
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


def demo_use_case_prompt_edit(user_input_body):
    """
    Prompt augmentation/engineering on case I. This is a patch work we did 
    for the demo. For the demo use case (workflow) I, the model needs a help. 
    If the input does not have '\\', need to add the '\\' back in the right place.
    
    :param user_input_body:
    :return user_input_body:
    """    
    has_use_case_1_device = user_input_body.find('MRE-Edge2.cisco.com') >= 0
    has_use_case_1_sentence = user_input_body.find('never establishes') >= 0
    has_backslashes = user_input_body.find('\\') >= 0    
    if has_use_case_1_device and has_use_case_1_sentence and not has_backslashes:
        use_case_1_body_splitted = user_input_body.split('never establishes.')
        use_case_1_body = use_case_1_body_splitted[0] + '\\ never establishes.' + use_case_1_body_splitted[1]
        user_input_body = use_case_1_body
    return user_input_body


def _try_convert_to_list(topic_output_json, key):
    """
    :param topic_output_json:
    :param key:
    :return key_list
    """
    if not isinstance(topic_output_json[key], list):
        try:
            key_list = ast.literal_eval(topic_output_json[key])
            # if not isinstance(key_list, list):
            #     import pdb; pdb.set_trace()
        except:
            key_list = [topic_output_json[key]]
            # import pdb; pdb.set_trace()
    else:
        key_list = topic_output_json[key] 
        
        # the topic_output_json[key] is Dict ..
        if isinstance(key_list, dict):
            key_list = [f'{k}. {v}' for k, v in key_list.items()]
        
    return key_list       
        

def papyrus_output_regex_formatting(topic_output_json, user_response, key_pair = ['Command', 'Signature']):
    """ 
    Here assume the first component in key_pair is the start word, and 
    the second component in key_pair is the end word.
    
    :param topic_output_json:
    :param user_response:
    :param key_pair:
    :return user_response_list_trunc:
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
                
                user_response_list.append({'Command': cmd_clean, 'Signature': seg_1_clean})
                user_response_list.extend([{'Command': '', 'Signature': t_} for t_ in segments[2:]])

            elif len(sub): 
                user_response_list.append({'Command': sub})
    else:
        user_response_list.append({'raw_summary': user_response})    

    user_response_list_trunc = user_response_list[:3]
    return user_response_list_trunc



def papyrus_output_solution_formatting(user_input_body, user_response_solution):
    """
    Output formatting. This is a patch work we did for the demo. For the demo, 
    the model needs a help. These are the manual hard-coded rules to format the 
    output correctly.

    TODO: split if needed? instead of wrapping it as a list?
    TODO: this is for the demo only... need to generalize.
    
    :param user_input_body:
    :param user_response_solution:
    :return final_list:
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
            # print(user_response_solution)
            final_list = []
            user_response_solution_list = [sentence.strip() for sentence in user_response_solution.split('later')]
            sent1 = [f"{user_response_solution_list[0]} later."]
            sentr = [sub for sub in user_response_solution_list[1].split('.')]
            final_list = sent1.extend(sentr[1:-1])
            final_list = sent1
            final_list[1] += final_list[2]+"." 
            final_list[2] = final_list[-1]+"."
            final_list = final_list[:3]
            final_list = [s.strip() for s in final_list]
        
        return final_list
    except:
        final_list = [user_response_solution]
        return final_list

    
if __name__ == "__main__":
    # testPipeline()
    app.run(debug=True, host='0.0.0.0', port=2222)
