import os
import logging


os.environ['CUDA_VISIBLE_DEVICES'] = '0'


import torch


class PapyrusModel():
    def __init__(self, lora_model_path, base_model_path=None, model_merged=False):
        """
        :param lora_model_path:
        :param base_model_path:
        :param model_merged:
        """
        self.lora_model_path = lora_model_path
        self.model_merged = model_merged
        self.base_model_path = base_model_path

    # def _prepare_results(self, outcomes, generation_indication):
    #     """
    #     Reorganize the results and only focus on generated prompts part
        
    #     :param outcomes:
    #     :param generation_indication: Not used...
    #     :return generation:
    #     """
    #     generation = []
    #     for idx, sub in enumerate(outcomes):
    #         if 'Signature:' in sub:
    #             generation.append(sub.split('Signature:\n')[-1])
    #         elif 'Solution:' in sub:
    #             generation.append(sub.split('Solution:\n')[-1])
    #         elif 'Section:' in sub:
    #             generation.append(sub.split('Section:\n')[-1])
    #     return generation
        
    def generate(
        self, 
        model,
        tokenizer,
        inputs, 
        generation_indication, 
        generation_config=None):
        """
        :param model:
        :param tokenizer:
        :param inputs:
        :param generation_indication:
        :param generation_config:
        :return final_outcome:
        """
        assert generation_indication in ['regex', 'solution', 'solution_with_code'], 'out of generation scope!'

        self.model = model
        self.tokenizer = tokenizer

        if not generation_config:
            generation_config={}
            generation_config['do_sample'] = {
                'regex': False,
                'solution': False,
                'solution_with_code': False
            }
            generation_config['max_new_tokens'] = {
                'regex': 90,
                'solution': 120,
                'solution_with_code': 500
            }
            generation_config['max_length'] = {
                'regex': 300,
                'solution': 120,
                'solution_with_code': 500
            }
            generation_config['temperature'] = {
                'regex': 0.0001, 
                'solution': 0.2,
                'solution_with_code':0,
            }
            generation_config['top_p'] = {
                'regex': 0.97,
                'solution': 1.0,
                'solution_with_code': 0.9
            }
            generation_config['repetition_penalty'] = {
                'regex': 1.2,
                'solution': 1.5,
                'solution_with_code': 1.4,
            }
        
        # set the model as evaluation status
        self.model.eval()
            
        # start the generation
        logging.info(f"the generation type is {generation_indication}")
        logging.info(f"the generation configuration is {generation_config}")
        
        final_outcome = []
        with torch.no_grad():
            inputs = self.tokenizer(
                inputs, return_tensors="pt", padding=True, truncation=True).to('cuda')
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=generation_config['max_new_tokens'][generation_indication],
                repetition_penalty=generation_config['repetition_penalty'][generation_indication],
                pad_token_id=self.tokenizer.eos_token_id)
             
            outcomes = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
             
        for idx, sub in enumerate(outcomes):
            final_outcome.append(sub.split('Section:\n')[-1])
            
        return final_outcome

