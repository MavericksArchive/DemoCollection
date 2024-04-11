import json


from flask import Flask, request, jsonify


from setup import read_yaml
from intention_utils import load_config
from intention_module_light import IntentionModuleLight


def load_intention_model():
    """
    Load intention_model_light 
    
    :return intention_model
    """
    # load intention_model
    print(f' *** Loading the intention model ... ')
    config = 'config/intention_module_config.yaml'
    config_output = read_yaml(config)
    templates = {key: read_yaml(value) for key, value in config_output.get('template', {}).items()}
    assert templates  # check if the templates are loaded correctly
    
    intention_model = IntentionModuleLight(config_output, templates)    
    print(f' *** Loaded the intention model light')
    print(f'llm: {intention_model}')
    return intention_model


def run_unitrun(query, llm, history=[]):
    """
    One single unit run for the intention module
    
    :param query:
    :param llm:
    :param history:
    :return unitrun_output:
    :return history:
    """
    topic_module_output = {}
    res = llm.run_light(query)
    topic_module_output['content'] = json.dumps(res)
        
    unitrun_output = {
        'query': query,
        'topic_module_output': topic_module_output,
        'answer': topic_module_output['content'],
    }
    history.append(unitrun_output)
            
    return unitrun_output, history


def run_intention_module(query, llm, history=[]):
    """
    Run the single intention module up to a threshold in max_conv_count.

    :param query:
    :param llm:
    :param history:
    :return intention_module_output:
    """
    CONV_COUNT = len(history)
    max_conv_count = 20000
    
    while CONV_COUNT < max_conv_count:
        unitrun_output, history = run_unitrun(query, llm, history)
        intention_module_output = {
            'answer': unitrun_output['answer'],
            'history': history
        }
        return intention_module_output


# load llm and config
config = load_config()
intention_model = load_intention_model()

HISTORY = []

app = Flask(__name__)
       

@app.route('/dev', methods=['POST'])
def dev():
    # api key    
    api_key = request.headers.get('X-Api-Key')    
    if api_key != '230e2b5e-fb08-405c-b9d2-f17e66be3b47':
        return jsonify({
        "message": json.loads(json.dumps('Forbidden'))
    }), 403                      

    # user input    
    data = request.get_json(force=True)
    user_input = data['user_input']
    
    intention_module_output = run_intention_module(user_input, llm=intention_model, history=HISTORY)
    
    verbose = False 
    if verbose:
        for i in range(len(HISTORY)):
            print(f'===== Conversation #{i} =====')
            for k, v in HISTORY[i].items(): print(f'{k}: {v}')

    if intention_module_output.get('answer'): 
        message = f"{intention_module_output.get('answer')}"
    else:
        raise Exception('Check the intention_module_output')

    resp = jsonify({"message": json.dumps(message, default=vars)})
    resp.status_code = 200
    return resp 


@app.route('/health', methods=['GET'])
def health():
    # api key    
    api_key = request.headers.get('X-Api-Key')    
    if api_key != '230e2b5e-fb08-405c-b9d2-f17e66be3b47':
        return jsonify({
        "message": json.loads(json.dumps('Forbidden'))
    }), 403                      

    resp = jsonify({"message": json.dumps('[intentionGPT35] Hello! Up and running', default=vars)})
    resp.status_code = 200
    return resp 


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)
