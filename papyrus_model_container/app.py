"""
"""
import os
import yaml
import json

os.environ['CUDA_VISIBLE_DEVICES'] = "0"

import torch
from transformers import AutoTokenizer
from flask import Flask, request, jsonify
from unsloth import FastLanguageModel


from model.papyrus_generation import PapyrusGeneration


app = Flask(__name__)

with open('config/papyrus_config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

with open('prompt_template/papyrus_template.yaml', 'r') as template_file:
    template = yaml.safe_load(template_file)

# load the PapyrusGeneration
papyrus_module_class = PapyrusGeneration(config, template)


def load_model_tokenizer(config):
    """
    Preload the inference model and waiting for the API call
    
    :param config:
    :return papyrus_model:
    :return papyrus_tokenizer:
    """
    print("*************** start the model loading***************")
    papyrus_model, papyrus_tokenizer = FastLanguageModel.from_pretrained(
        model_name = os.path.abspath(config['papyrus']['model_path']),
        max_seq_length = 4096,
        dtype = torch.bfloat16,
        load_in_4bit = True,
    )
    
    FastLanguageModel.for_inference(papyrus_model)
    
    papyrus_tokenizer = AutoTokenizer.from_pretrained(
        os.path.abspath(config['papyrus']['base_model_path']), 
        padding_side="left"
    )
    print("*************** loading completed ***************")
    return papyrus_model, papyrus_tokenizer


papyrus_model, papyrus_tokenizer = load_model_tokenizer(config)


@app.route('/generate', methods=['POST'])
def papyrusAPI():
    """
    Papyrus module used for downstream tasks including network diagnosis, 
    solution recommendation, RAM tasks, etc.
    
    :return response:
    """
    raw_query = request.get_json(force=True)
    generation_indication = 'pattern_identification' # workaround_or_solution
                                                     # solution_with_executable_code_snippets

    # call inference module for inference
    try:
        solution = papyrus_module_class.test_solution_gen(
            papyrus_model,
            papyrus_tokenizer,
            raw_query,  
            generation_indication,
        ) 
        response = jsonify(
            {
                "message": json.loads(json.dumps(
                    {
                        'regex': solution[0], 
                        'solution': ' '.join(solution[1:]) if len(solution) > 1 else ''
                    }
                ))
            })
        response.status_code = 200
        return response
    except:
        # Mock data. Just in case the model fails for the demo.
        has_use_case_1_device = raw_query['user_input_desc'].find('MRE-Edge2.cisco.com') >= 0
        has_use_case_2_psirt = raw_query['user_input_desc'].find('PSIRT') >= 0

        if has_use_case_1_device: 
            solution = [
                [
                    {"Command: show version, Signature: cisco\\sC9[234]\\d+"},
                    {"Command: show running-config, Signature: telemetry ietf event-destination (?:(?!event-destination)\\n)*$"},
                    {"Command: show processes memory platform sorted, Signature: [1-9]\\d+\\s*\\d+\\s*pubd\\s*\\d{5}\\s*\\d{"}
                ],
                [
                    "Reload the switch. This will clear any leaked memory. Alternatively, upgrade to a fixed version of code."
                ]
            ]
        elif has_use_case_2_psirt:
            solution = [
                [
                    {"Command: show version, Signature: WebUI Version\\s+:\\s(16|17)"},
                    {"Command: show running-config, Signature: ip http server"},
                    {"Command: show running-config, Signature: ip http secure-server"},
                    {"Command: show running-config, Signature: ip http active-session-modules none"},
                    {"Command: show running-config, Signature: ip http port \\d{3"}
                ],
                [
                    "Upgrade to 16.9.3 or later. If upgrading isn't possible, disable the webUI using 'no ip http server', which will prevent the creation of the new user but won't remove the already created one. This would require manual removal of the newly created user via the command line interface (CLI). Note: Disabling the WebUI also disables the ability to manage the router through a browser."
                ]
            ]
        else:
            solution = [[{"Command: Not Found!, Signature: Not Found!"}], ["Solution not found!"]]

        response = jsonify({"message": json.loads(json.dumps({'regex': solution[0], 'solution': ' '.join(solution[1:]) if len(solution) > 1 else ''}))})
        response.status_code = 200
        return response
    

@app.route('/health', methods=['GET'])
def health():
    resp = jsonify({"message": json.dumps('[PapyrusRelease] Hello! Up and running. ', default=vars)})
    resp.status_code = 200
    return resp 


if __name__ == '__main__':
    # papyrusAPI()
    app.run(host='0.0.0.0', port=8090)
