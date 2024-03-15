import os
import yaml
import json
from flask import Flask, request, jsonify


from beyond_one_cell_v2 import run_topic_module


# Initialize the Flask application
app = Flask(__name__)

HISTORY = []
CONV_COUNT = 0

def load_config():
    # Default configuration file
    config_file = 'config/topic_module_config.yaml'
    # Override if an environment variable is set
    if 'CONFIG_FILE' in os.environ:
        config_file = os.environ['CONFIG_FILE']
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        config = config['bice_encoder']
        return config

config = load_config()
print(f"Load config:")
print(config)



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
    
    topic_module_output = run_topic_module(user_input, history=HISTORY)
    CONV_COUNT = len(HISTORY)
        
    for i in range(len(HISTORY)):
        print(f'===== Conversation #{i} =====')
        for k, v in HISTORY[i].items(): print(f'{k}: {v}')
        
    # import pdb; pdb.set_trace()
    if topic_module_output.get('generated_sol'):
        message = f"###This is my message #{CONV_COUNT}.\n###{topic_module_output.get('generated_sol')}"
    elif topic_module_output.get('fqs'): 
        message = f"###This is my message #{CONV_COUNT}.\n###{topic_module_output.get('fqs')}"
    return jsonify({
        "message": json.loads(json.dumps(message))
    }), 200



if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=8888)