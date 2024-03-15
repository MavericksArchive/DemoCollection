import os

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
# from accelerate import Accelerator
import logging

from transformers import StoppingCriteria

# def a stop criteria 

# class MyStoppingCriteria(StoppingCriteria):
#     def __init__(self, target_sequence, prompt):
#         self.target_sequence = target_sequence
#         self.prompt=prompt

#     def __call__(self, input_ids, scores, **kwargs):
#         # Get the generated text as a string
#         generated_text = tokenizer.decode(input_ids[0])
#         generated_text = generated_text.replace(self.prompt,'')
#         # Check if the target sequence appears in the generated text
#         if self.target_sequence in generated_text:
#             return True  # Stop generation

#         return False  # Continue generation

#     def __len__(self):
#         return 1

#     def __iter__(self):
#         yield self


class PapyrusModel():
    def __init__(self, 
                 lora_model_path, 
                 base_model_path=None,
                 model_merged=False, ):
        
        self.lora_model_path = lora_model_path
        self.model_merged = model_merged
        self.base_model_path = base_model_path

    def _prepare_results(self, 
                         outcomes, 
                         generation_indication):
        """
          reorgnize the results and only focus on generated prompts part
        """
        generation = []
        
        for idx, sub in enumerate(outcomes):
            if 'Signature:' in sub:
                generation.append(sub.split('Signature:\n')[-1])
            elif 'Solution:' in sub:
                generation.append(sub.split('Solution:\n')[-1])
            elif 'Section:' in sub:
                generation.append(sub.split('Section:\n')[-1])
        return generation
        

    def generation(self, 
                   model,
                   tokenizer,
                   inputs, 
                   generation_indication, 
                   generation_config=None):
        
        assert generation_indication in ['regex', 'solution', 'solution_with_code'], 'out of generation scope!'

        self.model=model
        self.tokenizer=tokenizer

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
        
        # accelerator = Accelerator()

        final_outcome = []
        with torch.no_grad():
             inputs = self.tokenizer(inputs, return_tensors="pt", padding=True, truncation=True).to('cuda')
             outputs = self.model.generate(**inputs, max_new_tokens=generation_config['max_new_tokens'][generation_indication],
                                                    # do_sample=generation_config['do_sample'][generation_indication], 
                                                    # temperature=generation_config['temperature'][generation_indication], 
                                                    # top_p=generation_config['top_p'][generation_indication],
                                                    repetition_penalty=generation_config['repetition_penalty'][generation_indication],
                                                    pad_token_id=self.tokenizer.eos_token_id)
             
             outcomes = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
             
        for idx, sub in enumerate(outcomes):
            final_outcome.append(sub.split('Section:\n')[-1])
            
        # outcomes = self._prepare_results(outcomes,generation_indication)

        return final_outcome
        
        
    
