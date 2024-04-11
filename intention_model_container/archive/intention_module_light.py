"""
This module tries to do the followings
 - split the text/code 
 - perform the code analysis if codes exit
     - first split the prompt/command/parameters
     - cli prompt 
     - cli command and meaning
     - cli parameters and meaning
 - interprete the code if codes exist
 - understand and generate user's intention
 - understand and generate user's main question
 - generate knowledge

"""
import sys 
import sys 
import logging
from typing import List, Dict
from time import time

from langchain.embeddings import SentenceTransformerEmbeddings

EMBEDDING_MODEL = "all-MiniLM-L6-v2" 
embedding = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)

# sys.path.append('..')
# from util.setup import read_yaml, setup_logging
# from tools.topic_module import TopicModule

from setup import read_yaml, setup_logging
from topic_module import TopicModule


class TopicModuleLight(TopicModule):
    def __init__(self, config, templates: Dict):
        """
        Light model
        
        - Cisco Chat AI (GPT-3.5) for the LLM model
        """
        super().__init__(config, templates)
        
    def run_light(self, user_input):
        start_time = time()
        description = user_input

        intention_question = self.generate_intention_question_situation_no_code_id(
            question=description, type='zeroshot')        
                
        # output object
        topic_module_output = {
            "user_input_desc": description,
            "goal": intention_question.get('goal', ''),
            'main_question': intention_question.get('main_question', ''),
            'major_problem': intention_question.get('major_problem', ''),
            'situation': intention_question.get('situation', ''),
            'summary': intention_question.get('summary', ''),
            'extracted_entity': intention_question.get('extracted_entity', []),
            'system_message': intention_question.get('system_message', []),
            'steps': intention_question.get('steps', []),
            'solutions': intention_question.get('solutions', []),
            }        
        if self.config['kb']['kg']:
            topic_module_output['triplets'] = self.conversation_with_kg.memory.kg.get_triples()
        
        elapsed_time = time() - start_time
        logging.info(f'*** Time elapsed for run_light (inference): {elapsed_time} seconds ***')
        return topic_module_output 
        
