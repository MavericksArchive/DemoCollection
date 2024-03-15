import os
import yaml
import json
# from pathlib import Path
# import secrets


from flask import Flask, request, jsonify #, session

from beyond_one_cell_v5 import run_topic_module
from topic_module_light import TopicModuleLight
from setup import read_yaml
    
import warnings

# Ignore specific warning from logger
warnings.filterwarnings('ignore', category=DeprecationWarning)


def load_config():
    print(f' *** Loading the config ... ')
    # Default configuration file
    config_file = 'config/topic_module_config.yaml'
    # Override if an environment variable is set
    if 'CONFIG_FILE' in os.environ:
        config_file = os.environ['CONFIG_FILE']
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        print(f' *** Loaded the config')
        # print(f'config: {config}')
        return config
    

def load_topic_module():
    """
    """
    # load topic_module_light
    print(f' *** Loading the topic module light ... ')
    
    config = 'config/topic_module_config.yaml'
    config_output = read_yaml(config)
    templates = {key: read_yaml(value) for key, value in config_output.get('template', {}).items()}
    assert templates  # check if the templates are loaded correctly
    
    topic = TopicModuleLight(config_output, templates)
    # import pdb;pdb.set_trace()
    print(f' *** Loaded the topic module light')
    print(f'llm: {topic}')
    return topic


# load llm and config
topic = load_topic_module()
config = load_config()

# Initialize the Flask application
app = Flask(__name__)
       
HISTORY = []
CONV_COUNT = 0


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
    
    # topic_module_output = run_topic_module(user_input, llm=TopicLLM, history=HISTORY)
    topic_module_output = run_topic_module(user_input, llm=topic, history=HISTORY)
    CONV_COUNT = len(HISTORY)
        
    for i in range(len(HISTORY)):
        print(f'===== Conversation #{i} =====')
        for k, v in HISTORY[i].items(): print(f'{k}: {v}')
        
    # if topic_module_output.get('generated_sol'):
    #     message = f"###This is my message #{CONV_COUNT}.\n###{topic_module_output.get('generated_sol')}"
    # elif topic_module_output.get('fqs'): 
    #     message = f"###This is my message #{CONV_COUNT}.\n###{topic_module_output.get('fqs')}"
    # elif topic_module_output.get('answer'): 
    #     message = f"###This is my message #{CONV_COUNT}.\n###{topic_module_output.get('answer')}"
    # else:
    #     raise Exception('Check the topic_module_output')
    if topic_module_output.get('generated_sol'):
        message = f"{topic_module_output.get('generated_sol')}"
    elif topic_module_output.get('fqs'): 
        message = f"{topic_module_output.get('fqs')}"
    elif topic_module_output.get('answer'): 
        message = f"{topic_module_output.get('answer')}"
    else:
        raise Exception('Check the topic_module_output')

    resp = jsonify({"message": json.dumps(message, default=vars)})
    resp.status_code = 200
    return resp 


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    # This function will catch all other routes not explicitly defined
    return jsonify({
        "message": "Welcome to the ML prediction service. Use the /predict endpoint to make predictions."
    }), 200


if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=8888)