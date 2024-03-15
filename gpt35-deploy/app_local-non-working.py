import os
import yaml
import json
from pathlib import Path
import secrets


from flask import Flask, request, jsonify, session


# from beyond_one_cell_v2 import run_topic_module
from beyond_one_cell_v3 import run_topic_module

import warnings

# Ignore specific warning from logger
warnings.filterwarnings('ignore', category=DeprecationWarning)


# load LLM
# session['TopicLLM'] = None 


def load_config():
    print(f' *** Loading the config ... ')
    # Default configuration file
    config_file = 'config/topic_module_config.yaml'
    # Override if an environment variable is set
    if 'CONFIG_FILE' in os.environ:
        config_file = os.environ['CONFIG_FILE']
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        config = config['bice_encoder']
        print(f' *** Loaded the config')
        return config
    

def load_llm():
    """
    """
    # load topic_module_light
    print(f' *** Loading the topic module light ... ')
    import sys
    sys.path.append('..')
    from tools.topic_module_light import TopicModuleLight
    from util.setup import read_yaml
    
    config = 'config/topic_module_config.yaml'
    config_output = read_yaml(config)
    templates = {key: read_yaml(value) for key, value in config_output.get('template', {}).items()}
    assert templates  # check if the templates are loaded correctly
    
    topic = TopicModuleLight(config_output, templates)
    # import pdb;pdb.set_trace()
    session['TopicLLM'] = topic
    print(f' *** Loaded the topic module light')
    # running ... 
    # topic_module_output = topic.run_light(user_input)

load_llm()

# Initialize the Flask application
app = Flask(__name__)


# session
SECRET_FILE_PATH = Path(".flask_secret")
try:
    with SECRET_FILE_PATH.open("r") as secret_file:
        app.secret_key = secret_file.read()
except FileNotFoundError:
    # Let's create a cryptographically secure code in that file
    with SECRET_FILE_PATH.open("w") as secret_file:
        app.secret_key = secrets.token_hex(32)
        secret_file.write(app.secret_key)
     
       
HISTORY = []
CONV_COUNT = 0


config = load_config()
print(f"Load config:")
print(config)


# with app.app_context():
#     if not session.get('TopicLLM'):
#         print('TopicLLM is None. Loading it ...')
#         load_llm()
#         print('TopicLLM is None. Loaded it.')

        
@app.route('/dev', methods=['POST'])
def dev():
    
    # api key    
    api_key = request.headers.get('X-Api-Key')    
    if api_key != '230e2b5e-fb08-405c-b9d2-f17e66be3b47':
        return jsonify({
        "message": json.loads(json.dumps('Forbidden'))
    }), 403                      

    # LLM
    if not session.get('TopicLLM'):
        print(' *** ATTENTION *** TopicLLM is None. Loading it again...')
        load_llm()
        print(' *** ATTENTION *** TopicLLM is None. Loaded it again.')
    
    # user input    
    data = request.get_json(force=True)
    user_input = data['user_input']
    
    print(f'Trying to get the session.get("TopicLLM")')
    TopicLLM = session.get('TopicLLM')
    # import pdb;pdb.set_trace()
    print(f'Successfully got the session.get("TopicLLM")')
    
    topic_module_output = run_topic_module(user_input, llm=TopicLLM, history=HISTORY)
    # import pdb;pdb.set_trace()
    CONV_COUNT = len(HISTORY)
        
    for i in range(len(HISTORY)):
        print(f'===== Conversation #{i} =====')
        for k, v in HISTORY[i].items(): print(f'{k}: {v}')
        
    
    if topic_module_output.get('generated_sol'):
        message = f"###This is my message #{CONV_COUNT}.\n###{topic_module_output.get('generated_sol')}"
    elif topic_module_output.get('fqs'): 
        message = f"###This is my message #{CONV_COUNT}.\n###{topic_module_output.get('fqs')}"
    else:
        raise Exception('Check the topic_module_output')

    import pdb; pdb.set_trace()
    # return jsonify({"message": json.loads(json.dumps(message))}), 200
    # resp = jsonify({"message": json.loads(json.dumps(message))})
    resp = jsonify({"message": json.dumps(message, default=vars)})
    resp.status_code = 200
    return resp 




if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=8888)