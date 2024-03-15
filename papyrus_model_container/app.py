import os
import logging
import yaml
import json

os.environ['CUDA_VISIBLE_DEVICES'] = "0"

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
# from unsloth import FastLanguageModel
# from accelerate import Accelerator
# from accelerate.utils import gather_object

from flask import Flask, request, jsonify
from model.papyrus_generation import PapyrusGeneration
from unsloth import FastLanguageModel

# os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"


app = Flask(__name__)

# pre-load the inference model and waiting for the API call
with open('model/config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)
with open('model/template.yaml', 'r') as template_file:
    template = yaml.safe_load(template_file)

papyrus_module_class = PapyrusGeneration(config, template)

# accelerator = Accelerator()

print("*************** start the model loading***************")
# print(os.path.abspath(config['papyrus']['model_path']))
# print(config['papyrus']['base_model_path'])
# print(os.getcwd())
PapyrusModel, PapyrusTokenizer = FastLanguageModel.from_pretrained(
        model_name = os.path.abspath(config['papyrus']['model_path']),
        max_seq_length = 4096,
        dtype = torch.bfloat16,
        load_in_4bit = True,
    )
FastLanguageModel.for_inference(PapyrusModel)
PapyrusTokenizer = AutoTokenizer.from_pretrained(os.path.abspath(config['papyrus']['base_model_path']), padding_side="left")

print("*************** loading completed ***************")

@app.route('/generate', methods=['POST'])
def papyrusAPI():
    """ Papyrus module used for downstream tasks including network diagnosis, solution recommendation,
        RAM tasks, etc.
    """
    raw_query  = request.get_json(force=True)
    generation_indication='pattern_identification' # workaround_or_solution
                                                   # solution_with_exectuable_code_snippets

    # call inference module for inference
    try:
        solution = papyrus_module_class.test_solution_gen(
                                                        PapyrusModel,
                                                        PapyrusTokenizer,
                                                        raw_query,  
                                                        generation_indication,
                                                        ) 
        response = jsonify({"message": json.loads(json.dumps({'regex': solution[0], 'solution': ' '.join(solution[1:]) if len(solution) > 1 else ''}))})
        response.status_code = 200
   
        return response
    except:
        has_use_case_1_device = raw_query['user_input_desc'].find('MRE-Edge2.cisco.com') >= 0
        has_use_case_2_psirt = raw_query['user_input_desc'].find('PSIRT') >= 0

        if has_use_case_1_device: 
            solution = [[{"Command: show version, Signature: cisco\\sC9[234]\\d+"},
                        {"Command: show running-config, Signature: telemetry ietf event-destination (?:(?!event-destination)\\n)*$"},
                        {"Command: show processes memory platform sorted, Signature: [1-9]\\d+\\s*\\d+\\s*pubd\\s*\\d{5}\\s*\\d{"}],
                        ["Reload the switch. This will clear any leaked memory. Alternatively, upgrade to a fixed version of code."]
                        ]
        elif has_use_case_2_psirt:
            solution = [[{"Command: show version, Signature: WebUI Version\\s+:\\s(16|17)"},
                         {"Command: show running-config, Signature: ip http server"},
                         {"Command: show running-config, Signature: ip http secure-server"},
                         {"Command: show running-config, Signature: ip http active-session-modules none"},
                         {"Command: show running-config, Signature: ip http port \\d{3"}],
                         ["Upgrade to 16.9.3 or later. If upgrading isn't possible, disable the webUI using 'no ip http server', which will prevent the creation of the new user but won't remove the already created one. This would require manual removal of the newly created user via the command line interface (CLI). Note: Disabling the WebUI also disables the ability to manage the router through a browser."]
            ]
        
        else:
            solution = [[{"Command: Not Found!, Signature: Not Found!"}], ["Solution not found!"]]

        response = jsonify({"message": json.loads(json.dumps({'regex': solution[0], 'solution': ' '.join(solution[1:]) if len(solution) > 1 else ''}))})
        response.status_code = 200
        return response
    
    

### used for lambda to run the container
# def lambda_handler(event, context):
#     import serverless_wsgi
#     return serverless_wsgi.handle_request(app.server, event, )

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def warning(path):
    # raise warning fls
    # or non-intented query.
    return jsonify({
        "message": "Welcome to the ML prediction service. Use the /generate endpoint to make predictions."
    }), 200

if __name__ == '__main__':
    # papyrusAPI()
    app.run(host='0.0.0.0', port=8090)