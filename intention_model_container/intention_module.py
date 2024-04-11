"""
"""
import json
import time
import logging
import pprint 
from typing import Dict


from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.embeddings import SentenceTransformerEmbeddings


EMBEDDING_MODEL = "all-MiniLM-L6-v2" 
embedding = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)


from cisco_chat_ai_base import CiscoChatAI


class IntentionModule():
    def __init__(self, config, templates: Dict):
        """
        - Cisco Chat AI (GPT-3.5) for the LLM model
        """
        # config
        self.config = config                
        
        # prompt templates
        self.intention_prompt = templates['intention_prompt']
        self.code_prompt = templates['code_prompt']
        self.eval_prompt = templates['eval_prompt']
        self.memory_prompt = templates['memory_prompt']
        
        # load
        self._load_llm_model()      # GPT-3.5
            
        # misc.
        self.sleep_time = self.config['llm']['sleep_time']   # sleep time between GPT-3.5 calls
        
    def _load_llm_model(self):
        """Instantiate and load the LLM model"""
        logging.info('loading the LLM (ChatGPT-3.5)')
        self.cisco_chat_ai = CiscoChatAI(verbose=True)
        self.cisco_chat_ai.load_llm_model()
        self.llm = self.cisco_chat_ai.llm
        logging.info('Successfully loaded the LLM (ChatGPT-3.5)')

    def _renew_llm_token(self):
        time_check = time.time()
        elapsed_time = time_check - self.cisco_chat_ai.token_start_time
        print(f'GPT token elapsed time: {elapsed_time} seconds')
        if elapsed_time >= self.cisco_chat_ai.token_renew_threshold_seconds:
            print('=====' * 20)
            print(' ')
            print(f'Renewing cisco chat ai auth token...')
            self.cisco_chat_ai._create_auth_token()             # renew
            self.cisco_chat_ai.token_start_time = time.time()  # reset the start time
            print(f'Successfully renewing cisco chat ai auth token')
            print(f'new start time: {self.cisco_chat_ai.token_start_time}')
            print(' ')
            print('=====' * 20)
            return True
        else:
            print('=====' * 20)
            print(' ')
            print(f'No need to renew...')
            print(f'elapsed_time: {elapsed_time}')
            print(f'token_renew_threshold_seconds: {self.cisco_chat_ai.token_renew_threshold_seconds}')
            print(' ')
            print('=====' * 20)
            return False

    def generate_intention_question_situation_no_code_id(self, question):
        """
        Used in Mar 2024 demo. I deleted other methods that were not used in the demo.
        
        :param question:
        :return json_result:
        """
        json_result = {}
        
        # renewing ..
        renew_time_kpi = time.time()
        renew_required = self._renew_llm_token()
        if renew_required:
            print(f'--------' * 20)
            print(f'Renewing LLM ... ')
            self.cisco_chat_ai.load_llm_model()
            self.llm = self.cisco_chat_ai.llm      # renew
            print(f'Successfully renewed LLM')
            renew_time_kpi_elapsed = time.time() - renew_time_kpi
            print(f'Time passed creating new auth token and renewing LLM: {renew_time_kpi_elapsed} seconds')
            print(f'--------' * 20)        
        
        logging.info('Generating user intention ... using `intention_understanding_no_code_template_id`')
        
        prompt = PromptTemplate(
            template=self.intention_prompt['intention']['intention_understanding_no_code_template_id_steps_sol_v3'],             
            input_variables=["question"])
        
        chain = prompt | self.llm | StrOutputParser() 
        
        def _invoking(chain, question):
            """
            Invoke the LLM chain.
            
            :param chain:
            :param question:
            """
            results = chain.invoke({"question": question})
            json_result = json.loads(results)
            logging.info(json_result.keys())  
            
            for key, value in json_result.items():
                pprint.pprint(f"{key}: {value}")
            
            logging.info('Successfully generated user intention')            
            return json_result
        
        # retry 
        no_of_trial, GPT_RETRY_MAX = 0, 10
        while True and (no_of_trial < GPT_RETRY_MAX):
            try:
                no_of_trial += 1
                json_result = _invoking(chain, question)
                return json_result
            except Exception as errmsg:
                logging.error(f'!!!ERROR!!! {errmsg}')
                print(f'GPT-3.5 error. Trying again... Retry #{no_of_trial}')
                time.sleep(3)
                continue
        
        # GPT failed. Return the empty json_result dictionary
        print('GPT_RETRY_MAX reached!')
        return json_result 
