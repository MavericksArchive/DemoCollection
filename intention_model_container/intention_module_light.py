"""
"""
import logging
from typing import List, Dict
from time import time

from langchain.embeddings import SentenceTransformerEmbeddings

EMBEDDING_MODEL = "all-MiniLM-L6-v2" 
embedding = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)

from intention_module import IntentionModule


class IntentionModuleLight(IntentionModule):
    def __init__(self, config, templates: Dict):
        """
        Light model
        
        - Cisco Chat AI (GPT-3.5) for the LLM model
        """
        super().__init__(config, templates)
        
    def run_light(self, user_input):
        start_time = time()

        intention_output = self.generate_intention_question_situation_no_code_id(
            question=user_input)
                
        intention_module_output = {
            "user_input_desc": user_input,
            "goal": intention_output.get('goal', ''),
            'main_question': intention_output.get('main_question', ''),
            'major_problem': intention_output.get('major_problem', ''),
            'situation': intention_output.get('situation', ''),
            'summary': intention_output.get('summary', ''),
            'extracted_entity': intention_output.get('extracted_entity', []),
            'system_message': intention_output.get('system_message', []),
            'steps': intention_output.get('steps', []),
            'solutions': intention_output.get('solutions', []),
            }        
        
        elapsed_time = time() - start_time
        logging.info(f'*** Time elapsed for run_light (inference): {elapsed_time} seconds ***')
        return intention_module_output 
        
