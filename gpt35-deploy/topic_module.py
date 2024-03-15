"""
Deploy test...


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
import json
import time
import logging
import pprint 
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv, find_dotenv
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.memory import ConversationKGMemory
from langchain.chains import ConversationChain
from langchain.tools import Tool
from langchain_community.utilities import GoogleSearchAPIWrapper

EMBEDDING_MODEL = "all-MiniLM-L6-v2" 
embedding = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)

from setup import read_yaml
from cisco_chat_ai_base import CiscoChatAI


class TopicModule():
    def __init__(self, config, templates: Dict):
        """
        - Cisco Chat AI (GPT-3.5) for the LLM model
        - RAG database I: (planned) hierarchical query of Qixu's embedding
        - (optional) RAG database II: crude production manual RAG DB
        - (optional) Google Search Tool         
        """
        # config
        self.config = config                
        self.bice_model_config = config['bice_encoder']
        
        # prompt templates
        self.intention_prompt = templates['intention_prompt']
        self.code_prompt = templates['code_prompt']
        self.eval_prompt = templates['eval_prompt']
        self.memory_prompt = templates['memory_prompt']
        
        # load
        self._load_llm_model()      # GPT-3.5
        if self.config['kb']['crude_rag_db']:
            logging.info('configured to the crude RAG DB')
            self._load_vectordb()        
        if self.config['kb']['search']:
            logging.info('configured to load the Google Search engine')
            self._load_search_engine()  
        if self.config['kb']['kg']:     # generated KG
            self._generate_kg_chain()
            
        # misc.
        self.sleep_time = self.config['llm']['sleep_time']   # sleep time between GPT-3.5 calls
        
    def _load_llm_model(self):
        """Load the LLM model"""
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
            self.cisco_chat_ai.create_auth_token()             # renew
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
        
    def _load_vectordb(self):
        """
        This is the crude production manual RAG DB 
        This is different from our hierarchical query
        """
        # vector db
        logging.info('loading the vectorDB (production manual)')
        self.vectordb = Chroma(
                    persist_directory=self.config['vectordb']['vector_db_path'], 
                    embedding_function=embedding)        
        logging.info('Successfully loaded the vectorDB (production manual)')

    def query_vectordb(self, query):
        """
        Query the vector DB. 
        
        :param query:
        :return :
        """
        logging.info('querying the vectorDB (production manual)')
        try:
            retriever = self.vectordb.as_retriever(
                search_type=self.config['vectordb']['vectordb_search_type'], 
                search_kwargs={"k": self.config['vectordb']['vectordb_no_of_docs']})

            unique_docs = retriever.invoke(query)
            logging.info(f'The number of pulled unique docs: {len(unique_docs)}')
            logging.info('Successfully queried the vectorDB (production manual)')
            if len(unique_docs) == 0:
                logging.warn('!!! Attention !!! No documents pulled ')
            return unique_docs
        except Exception as e :
            logging.info(f'!!! Error in test_chroma_query!!! {e}')

    def _load_search_engine(self):
        """Load the google search tool"""
        logging.info('loadig the Google Search API ... ')
        try:
            assert load_dotenv(find_dotenv(Path.home()/'doojung'/'.google'/'.env'))  # Load the .env file.
        except AssertionError as errmsg:
            logging.error(f"AssertionError! Env variable did not load!")
            raise
        
        # search_params
        # https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list
        search = GoogleSearchAPIWrapper()

        def top5_results(query):
            k = self.config['kb']['search_k']
            return search.results(query, k)

        self.google_search_snip_tool = Tool(
            name="Google Search Snippets",
            description="Search Google for recent results.",
            func=top5_results,
        )
        logging.info('Successfully loaded the Google Search API.')

    def run_google_search(self, query):
        """Run the google search with the query"""
        logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
        time.sleep(self.sleep_time)
        search_results = self.google_search_snip_tool.run(query)
        pprint.pprint(search_results)
        
        # filtering for the test example... "problem-local-authentication-in-cisco-catalyst-9200"
        search_results_filtered = [result for result in search_results if result['link'].find(
            'problem-local-authentication-in-cisco-catalyst-9200') < 0]
        
        for res in search_results_filtered:
            logging.info(f"TITLE: {res['title']}")
            logging.info(f"SNIPPET: {res['snippet']}")
            logging.info(f"URL: {res['link']}")
            logging.info(' ')
        return search_results_filtered

    def _generate_kg_chain(self):
        logging.info('Initializing the KG chain...')
        prompt = PromptTemplate(
            input_variables=["history", "input"], 
            template=self.memory_prompt['memory']['conv_kg_template'])
        self.conversation_with_kg = ConversationChain(
            llm=self.llm, 
            verbose=True, 
            prompt=prompt, 
            memory=ConversationKGMemory(llm=self.llm)
        )
        logging.info('Successfully initialized the KG chain')

    def _generate_multiquery(self, mq_template, mq_template_name, question):
        logging.info(f'generating multiquery with mq_template_name: {mq_template_name}')
        logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
        time.sleep(self.sleep_time)  
        prompt = PromptTemplate(template=mq_template, input_variables=["question"])
        chain = prompt | self.llm | StrOutputParser() 
        results = chain.invoke({"question": question})
        for idx, result in enumerate(results.split("\n"), 1):
            logging.info(f"query #{idx}: {result}")        
        logging.info(f'Successfully generated multiquery with mq_template_name: {mq_template_name}')
        return [result for result in results.split("\n") if result != '']

    def split_code_text(self, user_input, count=0, max_count=3):
        """
        if applicable, split the code and split
        
        TODO: error message can present. Currently treated as code snippet.. Should be parsed differently. 
        """
        logging.info('Splitting text and code from the user_input ... ')

        context = None
        type = self.code_prompt['code_desc_parse_template_type']
                
        if type == 'zeroshot':
            logging.info('split code/text: zeroshot')
            prompt = PromptTemplate(
                template=self.code_prompt['code']['code_desc_parse_template'], 
                input_variables=["question"])
            
            chain = prompt | self.llm | StrOutputParser() 
            results = chain.invoke({"question": user_input})
            try:
                json_result = json.loads(results)
                logging.info(json_result.keys())
                for key, value in json_result.items():
                    logging.info(f"{key}: {value}")
                logging.info('Successfully splitted text and code from the user_input.')
            except Exception as errmsg:
                logging.error(f'ERROR!!! {errmsg}')
                import pdb; pdb.set_trace()

        elif type == 'zeroshot_with_mq':
            logging.info('split code/text: zeroshot with multiquery')
            mq_results = self._generate_multiquery(
                self.code_prompt['code']['gen_mq_with_cocde_template'], 
                mq_template_name='mq_with_code', 
                question=user_input)
            context = '\n'.join(mq_results)
            
            prompt = PromptTemplate(
                template=self.code_prompt['code']['code_desc_parse_mq_template'],
                input_variables=["context", "question"])
            
            chain = prompt | self.llm | StrOutputParser() 
            results = chain.invoke({"context": context, "question": user_input})
            try:
                json_result = json.loads(results)
                logging.info(json_result.keys())
                for key, value in json_result.items():
                    logging.info(f"{key}: {value}")
                logging.info('Successfully splitted text and code from the user_input.')
            except Exception as errmsg:
                logging.error(f'ERROR!!! {errmsg}')
                import pdb; pdb.set_trace()
            
        elif type == 'zeroshot_with_rag':
            # zeroshot with RAG
            # may need to provide how to read the code, warning, errors, .. 
            logging.info('split code/text: zeroshot with RAG')
            # regex_retrieval = RegexRetrieval(
            #     vector_db_path=self.config['vectordb']['vector_db_path'],
            #     jsonl_docs_path='/home/ec2-user/doojung/external_datasets/docs.jsonl',
            #     manual_type='product_manual')

            # unique_docs = regex_retrieval.baseline_simple(user_input)
            # unique_docs = regex_retrieval.multiquery(user_input)
            # unique_docs = regex_retrieval.ensemble(user_input, bm25_nrows=50000, search_type='similarity')
            # vectordb retrieval production manual
            # try with the retrieved production manual
            retriever = self.vectordb.as_retriever()
            analyze_code_line_prompt = ChatPromptTemplate.from_template(code_line_analysis_template)
            chain = (
                {"context": retriever, "code": RunnablePassthrough()}
                | analyze_code_line_prompt
                | self.llm
                | StrOutputParser()
            )
            
            logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
            time.sleep(self.sleep_time)
            results = chain.invoke(code_line)
            import pdb; pdb.set_trace()             
        
        # TODO: universal critique and refine 
        # if critique:
        
        # check before we move one! 
        # if code cannot be found from the user_input, run it again...
        code_lines = json_result['code'].split('\n')
        
        # inspect
        is_line = True
        for line in code_lines:
            if (user_input.find(line) < 0):
                is_line = False
                break
            else:
                logging.info('!CHECK! split_code_text: line exists in the user_input. The check passed.')

        count = 0
        import numpy as np 
        while not is_line and count < max_count:
            logging.info(f'!Retry! split_code_text: count={count}\tmax_count={max_count}')
            if context:
                results = chain.invoke({"context": context, "question": user_input}) 
            else:
                results = chain.invoke({"question": user_input})
            count += 1
            try:
                json_result = json.loads(results)
                code_lines = json_result['code'].split('\n')
                inspection_result = [user_input.find(line) < 0 for line in code_lines]                
                if np.all([val > 0 for val in inspection_result]):
                    is_line = True
                else:
                    is_line = False                
                        
            except Exception as errmsg:
                logging.error(f'ERROR!!! {errmsg}')
                import pdb; pdb.set_trace()
        
        if self.config['kb']['kg']:
            kg_input = f"{json_result['description']}\n{json_result['code']}"
            _  = self.conversation_with_kg.predict(input=kg_input)
        
        # import pdb; pdb.set_trace()
        return json_result
    
    def analyze_code(self, code_lines: List) -> Dict:
        """
        What is code command, what are arguments to the code, what impact do those arguments cause? 
            - prompt
            - code command 
            - code arguements 
        
        :param code:
        :return code_understanding:
        """
        code_understanding = {}
        line_by_line_results = []
        holistic_understanding = ""

        if isinstance(code_lines, list):
            # set up
            code_line_analysis_template = self.code_prompt['code']['code_line_analysis_template']
            extracted_code = [code.strip('code:').strip(' ') for code in code_lines]
            no_of_lines = len(extracted_code)
            for idx, code_line in enumerate(extracted_code, 1):
                if code_line == '':
                    continue
                try:
                    logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
                    time.sleep(self.sleep_time)                            
                    logging.info(f'Entering analyzing each code line ...')
                    json_result = self._analyze_code_line(code_line, code_line_analysis_template)
                    json_result['code_line'] = code_line
                    line_by_line_results.append(json_result)  
                    logging.info(f'Line {idx}/{no_of_lines}: {code_line} is done.')
                except:
                    import pdb; pdb.set_trace()
        else:
            raise Exception('code_lines is not a list')

        # TODO: universal critique and refine 
        
        # aggregate understanidng holistically
        code_understanding_template = self.code_prompt['code']['code_understanding_template']
        holistic_understanding = self._understand_codes_as_whole(line_by_line_results, code_understanding_template)
        
        line_by_line_results_str = '\n'.join([result.get('explanation', '') for result in line_by_line_results])
        code_understanding = {
            "line_by_line_results_str": line_by_line_results_str,
            "holistic_understanding": holistic_understanding
            }
        logging.info(f'line_by_line_results: {line_by_line_results_str}')
        logging.info(f'holistic_understanding: {holistic_understanding}')
        return code_understanding
    
    def _analyze_code_line(self, code_line, code_line_analysis_template):
        """
        # RAG approach (v1 template)
        Analyze the code line using vector DB (production manual).
        
        :param code_line:
        :return code_line_understanding:
        """        
        # vectordb retrieval production manual
        # try with the retrieved production manual
        retriever = self.vectordb.as_retriever()
        analyze_code_line_prompt = ChatPromptTemplate.from_template(code_line_analysis_template)
        chain = (
            {"context": retriever, "code": RunnablePassthrough()}
            | analyze_code_line_prompt
            | self.llm
            | StrOutputParser()
        )
        
        logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
        time.sleep(self.sleep_time)
        results = chain.invoke(code_line)
        logging.info(f'below is the result from analyzing each code line:\n')
        # pprint.pprint(results)
        try:
            json_result = json.loads(results)
            print(json_result.keys())  # dict_keys(['prompt', 'command', 'parameters', 'explanation'])
            
            for key, value in json_result.items():
                pprint.pprint(f"{key}: {value}")
            
            return json_result

        except Exception as errmsg:
            logging.error(f'ERROR!!! {errmsg}')
            raise
            
        # TODO: universal critique and refine 
    
    def _understand_codes_as_whole(self, line_by_line_results, code_understanding_template):
        logging.info('Tyring to understand the codes as a whole.')
        logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
        time.sleep(self.sleep_time)        
        
        # preprocessing the input               
        retriever = self.vectordb.as_retriever()
        analyze_code_line_prompt = ChatPromptTemplate.from_template(code_understanding_template)
        chain = (
            {"context": retriever, "query_w_input": RunnablePassthrough()}
            | analyze_code_line_prompt
            | self.llm
            | StrOutputParser()
        )
        query = '\n'.join([result.get('explanation', '') for result in line_by_line_results])
        query_w_input = f'USER_INPUT: {self.user_input}\n\nCODE_INTERPRETATION: {query}'
        holistic_understanding = chain.invoke(query_w_input)
        
        # KG
        if self.config['kb']['kg']:
            _  = self.conversation_with_kg.predict(input=holistic_understanding)
            
        return holistic_understanding

    def generate_intention_question_situation_no_code(self, question):
        """Generate intention
        Here.. 
        # question = code_understanding['holistic_understanding']
        """
        logging.info('Generating user intention ... using `intention_understanding_no_code_template`')
        logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
        time.sleep(self.sleep_time)
        
        type = 'zeroshot_with_mq'
        
        if type == 'zeroshot':
            pass  

        if type == 'zeroshot_with_mq':
            logging.info(f'_generate_intention_question_situation with {type}')
            mq_results_str = self._understand_desc(question)
            question = f"{question}\n{mq_results_str}"
        
        
        prompt = PromptTemplate(
            template=self.intention_prompt['intention']['intention_understanding_no_code_template'], 
            input_variables=["question"])
        
        chain = prompt | self.llm | StrOutputParser() 
        results = chain.invoke({"question": question})

        try:
            json_result = json.loads(results)
            logging.info(json_result.keys())  
            
            for key, value in json_result.items():
                pprint.pprint(f"{key}: {value}")
            
            # KG
            if self.config['kb']['kg']:
                kg_input = f"{json_result['goal']}\n{json_result['situation']}\n{json_result['main_question']}"
                _  = self.conversation_with_kg.predict(input=kg_input)

            logging.info('Successfully generated user intention')            
            return json_result

        except Exception as errmsg:
            logging.error(f'ERROR!!! {errmsg}')
            raise
                
            
        # TODO: universal critique and refine 

    def generate_intention_question_situation_no_code_id(self, question, type='zeroshot_with_mq'):
        """Generate intention
        
        Used in Mar 2024 demo.
        
        # question = code_understanding['holistic_understanding']
        """
        json_result = {}
        
        # renewing experimenting..
        renew_time_kpi = time.time()
        renew_required = self._renew_llm_token()
        if renew_required:
            print(f'--------' * 20)
            print(f'Renewing LLM ... ')
            self.cisco_chat_ai.load_llm_model()
            self.llm = self.cisco_chat_ai.llm
            print(f'Successfully renewed LLM')
            renew_time_kpi_elapsed = time.time() - renew_time_kpi
            print(f'Time passed creating new auth token and renewing LLM: {renew_time_kpi_elapsed} seconds')
            print(f'--------' * 20)
        # renewing experimenting..
        
        
        logging.info('Generating user intention ... using `intention_understanding_no_code_template_id`')
        # logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
        # time.sleep(self.sleep_time)
        
        # type = 'zeroshot_with_mq'
        
        if type == 'zeroshot':
            pass  

        if type == 'zeroshot_with_mq':
            logging.info(f'_generate_intention_question_situation with {type}')
            mq_results_str = self._understand_desc(question)
            question = f"{question}\n{mq_results_str}"
        
        
        prompt = PromptTemplate(
            # template=self.intention_prompt['intention']['intention_understanding_no_code_template_id'], 
            # template=self.intention_prompt['intention']['intention_understanding_no_code_template_id_steps'], 
            # template=self.intention_prompt['intention']['intention_understanding_no_code_template_id_steps_sol'],     
            # template=self.intention_prompt['intention']['intention_understanding_no_code_template_id_steps_sol_v2'],             
            template=self.intention_prompt['intention']['intention_understanding_no_code_template_id_steps_sol_v3'],             
            input_variables=["question"])
        
        chain = prompt | self.llm | StrOutputParser() 
        
        def invoking(chain, question):
            # from json.decoder import JSONDecodeError
            # raise JSONDecodeError('Custom error', doc='my doc', pos=8888)
            # raise Exception('Customer error')
            results = chain.invoke({"question": question})
            json_result = json.loads(results)
            logging.info(json_result.keys())  
            
            for key, value in json_result.items():
                pprint.pprint(f"{key}: {value}")
            
            # KG
            if self.config['kb']['kg']:
                kg_input = f"{json_result['goal']}\n{json_result['situation']}\n{json_result['main_question']}"
                _  = self.conversation_with_kg.predict(input=kg_input)

            logging.info('Successfully generated user intention')            
            return json_result
        
        # retry 
        no_of_trial, GPT_RETRY_MAX = 0, 10
        while True and (no_of_trial < GPT_RETRY_MAX):
            try:
                no_of_trial += 1
                json_result = invoking(chain, question)
                return json_result
            except Exception as errmsg:
                logging.error(f'!!!ERROR!!! {errmsg}')
                print(f'GPT-3.5 error. Trying again... Retry #{no_of_trial}')
                time.sleep(3)
                continue
            break
        
        #
        # TODO:
        #
        #
        
        print(f'GPT_RETRY_MAX reached! ')
        
        # template approach for the demo 
        # workflow 1 
        # if user_input is workflow 1 
        # output = {'extracted_entity': ['MRE2.cisco.com', 'cat9200'], 'steps': ['', '', '',]}
        
        # workflow 7
        # if user_input is workflow 1 
        # output = {'extracted_entity': ['MRE2.cisco.com', 'cat9200'], 'steps': ['', '', '',]}
        
        return json_result
            
        # TODO: universal critique and refine    


    def _generate_intention_question_situation(self, question, code_interpretation):
        """
        Here..
        question = user_input
        code_interpretation = code_understanding['holistic_understanding']
        """
        logging.info('Generating user intention ... using `intention_understanding_template`')
        logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
        time.sleep(self.sleep_time)
        
        type = 'zeroshot_with_mq'
        
        if type == 'zeroshot':
            pass  

        if type == 'zeroshot_with_mq':
            logging.info(f'_generate_intention_question_situation with {type}')
            mq_results_str = self._understand_desc(question)
            question = f"{question}\n{mq_results_str}"
        
        prompt = PromptTemplate(
            template=self.intention_prompt['intention']['intention_understanding_template'], 
            input_variables=["code_interpretation", "question"])
        
        chain = prompt | self.llm | StrOutputParser() 
        results = chain.invoke({"code_interpretation": code_interpretation, "question": question})

        try:
            json_result = json.loads(results)
            logging.info(json_result.keys())  
            
            for key, value in json_result.items():
                pprint.pprint(f"{key}: {value}")
            
            # KG
            if self.config['kb']['kg']:
                kg_input = f"{json_result['goal']}\n{json_result['situation']}\n{json_result['main_question']}"
                _  = self.conversation_with_kg.predict(input=kg_input)

            logging.info('Successfully generated user intention')            
            return json_result

        except Exception as errmsg:
            logging.error(f'ERROR!!! {errmsg}')
            import pdb;pdb.set_trace()
                
            
        # TODO: universal critique and refine 
            
    def evaluate(self, question, has_code=False):
        logging.info('Evaluating ... ')
        logging.info(f'Cisco Chat AI GPT-3.5 sleep time: {self.sleep_time} seconds')
        time.sleep(self.sleep_time)
                
        # need to move to the base model.. or refine the base model method
        if has_code:
            # desc and code provided
            prompt = PromptTemplate(
                template=self.eval_prompt['evaluation']['eval_code_desc_template'], 
                input_variables=["question"])
            
            chain = prompt | self.llm | StrOutputParser() 
            results = chain.invoke({"question": question})        
            
        else:
            # desc provided only
            prompt = PromptTemplate(
                template=self.eval_prompt['evaluation']['eval_desc_template'], 
                input_variables=["question"])
            
            chain = prompt | self.llm | StrOutputParser() 
            results = chain.invoke({"question": question})        
        
        try:
            json_result = json.loads(results)
            logging.info(json_result.keys())
            
            for key, value in json_result.items():
                logging.info(f"{key}: {value}")

            # KG
            if self.config['kb']['kg']:
                kg_input = f"{json_result['evaluation']}\n{json_result['evaluation_reason']}"
                _  = self.conversation_with_kg.predict(input=kg_input)
            
            # assert len(json_result.keys()) == 2
            logging.info('Successfully evaluated')
            return json_result

        except Exception as errmsg:
            logging.error(f'ERROR!!! {errmsg}')
            import pdb; pdb.set_trace()
                
        # TODO: universal critique and refine 
                    
    def _generate_followup_questions(self, eval_json_result, max_count):
        """
        Trying to acquire more knowledge from the user
        """
        eval_result = eval_json_result['evaluation']
        
        raise NotImplementedError
    
        while str(eval_result) != 'True' or max_count < 3:
            # what is missing?
            pass 
            # retrieve the RAG/Search ... 
            pass 
        
        return None
        
    def _augment_the_knowledge(self, eval_json_result, max_count):
        """
        Trying to acquire more knowledgefrom RAG/Search
        """
        eval_result = eval_json_result['evaluation']
        raise NotImplementedError
    
        while str(eval_result) != 'True' or max_count < 3:
            # what is missing?
            pass 
            # retrieve the RAG/Search ... 
            pass 
        
        return None
    
    def _understand_desc(self, description):
        # TODO: process the input
        # intention..augmentation
        mq_results = self._generate_multiquery(
            self.intention_prompt['intention']['gen_mq_without_code_template'], 
            mq_template_name='mq_without_code', 
            question=description)
        if isinstance(mq_results, list):
            mq_results_str = '\n'.join(mq_results)
        return mq_results_str

    def run(self, user_input):
        # text/code split 
        code_lines = []
        errmsg_lines = []

        # TODO: code parser, errmsg parser run once 
        self.user_input = user_input
        output = self.split_code_text(user_input)
        description = output['description'] 
        code_lines = output['code'].split('\n')
        code_understanding = {}
        # TODO: the user input may have more than just code and text. Organize better.
        
        # understand
        if len(code_lines) == 1 and code_lines[0] == 'missing code':
            description_understanding = self._understand_desc(description)
        elif len(code_lines) >= 1:
            # if code exists, try to understand the code snippets
            code_understanding = self.analyze_code(code_lines)
        else:
            logging.warn(f'inspect the code_lines: {len(code_lines)}')
            import pdb;pdb.set_trace()
        
        # identify the intention
        if len(code_lines) == 1 and code_lines[0] == 'missing code':
            intention_question = self.generate_intention_question_situation_no_code(
                question=description_understanding)
        elif len(code_lines) >= 1:
            intention_question = self._generate_intention_question_situation(
                question=self.user_input, 
                code_interpretation=code_understanding['holistic_understanding'])
        else:
            logging.warn(f'inspect the code_lines: {len(code_lines)}')
            import pdb;pdb.set_trace()
        
        # inspect KG
        if self.config['kb']['kg']:
            for triplet in self.conversation_with_kg.memory.kg.get_triples():
                logging.info(triplet)
                
        # evaluate 
        if len(code_lines) == 1 and code_lines[0] == 'missing code':
            question = f"""GOAL: {intention_question['goal']}\nMAIN_QUESTION: {intention_question['main_question']}\nSITUATION: {intention_question['situation']}\nMAJOR_PROBLEM: {intention_question.get('major_problem', '')}"""
            eval_json_result = self.evaluate(question)
        elif len(code_lines) >= 1:
            question = f"""GOAL: {intention_question['goal']}\nMAIN_QUESTION: {intention_question['main_question']}\nSITUATION: {intention_question['situation']}\nMAJOR_PROBLEM: {intention_question.get('major_problem', '')}\nUNDERSTANDING: {code_understanding.get('holistic_understanding', '')}"""
            eval_json_result = self.evaluate(question, has_code=True)
        else:
            logging.warn(f'inspect the code_lines: {len(code_lines)}')
            import pdb;pdb.set_trace()

        # inspect KG
        if self.config['kb']['kg']:
            for triplet in self.conversation_with_kg.memory.kg.get_triples():
                logging.info(triplet)
                    
        # evaluation result
        eval_result = eval_json_result['evaluation']    

        # retrieve further 
        # TODO:
        # self._augment_the_knowledge()

        # generate follow up questions
        # TODO:
        # self._generate_followup_questions()

        # output object
        topic_module_output = {
            "user_input_desc": description,
            "user_input_code": code_lines,
            "goal": intention_question.get('goal', ''),
            'main_question': intention_question.get('main_question', ''),
            'major_problem': intention_question.get('major_problem', ''),
            'code_interpretation': code_understanding.get('holistic_understanding', ''),
            'code_line_by_line_results_str': code_understanding.get('line_by_line_results_str', ''),
            'eval': eval_json_result['evaluation'],
            'eval_reason': eval_json_result['evaluation_reason']
            }        
        if self.config['kb']['kg']:
            topic_module_output['triplets'] = self.conversation_with_kg.memory.kg.get_triples()
        
        logging.info(f'topic_module_output.keys(): {topic_module_output.keys()}')
        logging.info(f'topic_module_output.get("user_input_desc", ""): {topic_module_output.get("user_input_desc", "")}')
        logging.info(f'topic_module_output.get("user_input_code", ""): {topic_module_output.get("user_input_code", "")}')
        logging.info(f'topic_module_output.get("goal", ""): {topic_module_output.get("goal", "")}')
        logging.info(f'topic_module_output.get("main_question", ""): {topic_module_output.get("main_question", "")}')
        logging.info(f'topic_module_output.get("major_problem", ""): {topic_module_output.get("major_problem", "")}')
        logging.info(f'topic_module_output.get("code_interpretation", ""): {topic_module_output.get("code_interpretation", "")}')
        logging.info(f'topic_module_output.get("line_by_line_results", ""): {topic_module_output.get("code_line_by_line_results_str", "")}')
        logging.info(f'topic_module_output.get("eval", ""): {topic_module_output.get("eval", "")}')
        logging.info(f'topic_module_output.get("eval_reason", ""): {topic_module_output.get("eval_reason", "")}')
        if self.config['kb']['kg']:
            logging.info(f'topic_module_output.get("triplets", None): {topic_module_output.get("triplets", None)}')
        return topic_module_output 
        
