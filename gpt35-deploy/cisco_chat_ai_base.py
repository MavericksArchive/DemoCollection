"""
Cisco Chat AI API + LangChain
Deploy test...
"""
import os
import time
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

try:
    assert load_dotenv(find_dotenv('.env'))  # Load the .env file.
except AssertionError as errmsg:
    print(f"AssertionError! Env variable did not load!")
    raise 

import openai
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain  
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

os.environ["OPENAI_API_BASE"] = "https://chat-ai.cisco.com"
openai.api_type = "azure"
openai.api_version = "2023-03-15-preview"


class CiscoChatAI:
    """
    Cisco Enterprise Chat AI (Azure OpenAI API)
    https://onesearch.cisco.com/ciscoit/chatgpt/home
    """
    def __init__(
        self, 
        model_name="gpt-3.5-turbo", 
        engine_name="gpt-35-turbo",
        temperature=1e-24, #1e-24,
        verbose=False):
        
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.appkey = os.getenv("APP_KEY")
        self.user_dict = {"appkey" : self.appkey}
        assert isinstance(self.client_id, str)
        assert isinstance(self.client_secret, str)
        assert isinstance(self.appkey, str)
        self.url = "https://id.cisco.com/oauth2/default/v1/token"
        self.model_name = model_name
        self.engine_name = engine_name
        self.temperature = temperature
        self.verbose = verbose
        self.create_auth_token()
        self.token_renew_threshold_seconds = 2400  # seconds
        print(f'token_renew_threshold_seconds: {self.token_renew_threshold_seconds} seconds')

    def create_auth_token(self):
        """
        Cisco Chat AI auto token
        """
        
        self.token_start_time = time.time()  # initialize the time
        
        
        payload = "grant_type=client_credentials"
        value = base64.b64encode(
            f'{self.client_id}:{self.client_secret}'.encode('utf-8')
        ).decode('utf-8')
        
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {value}"
        }

        token_response = requests.request("POST", self.url, headers=headers, data=payload)
        self.token_response = token_response
        os.environ["OPENAI_API_KEY"] = token_response.json()["access_token"]
        if self.verbose:
            print(f"token_response token_type:\t{token_response.json()['token_type']}")
            print(f"token_response expires_in:\t{token_response.json()['expires_in']}")
            print(f"token_response access_token[-10:]:\t{token_response.json()['access_token'][-10:]}")
            print(f"Successfully created the auth token")
        
    def load_llm_model(self):
        """
        langchain's ChatOpenAI
        """
        self.llm = ChatOpenAI(
            temperature=self.temperature,
            model_kwargs=dict(
                engine=self.engine_name,
                stop=["<|im_end|>"],
                user=json.dumps(self.user_dict),
                seed=23456,
                top_p=1e-24 
            )
        )
        if self.verbose:
            print(f"llm.model_name: {self.llm.model_name}")
            print(f"llm.temperature: {self.llm.temperature}")
            print(f"llm.model_kwargs: {self.llm.model_kwargs}")
            print(f"llm.openai_api_key[-10:]: {self.llm.openai_api_key[-10:]}")
            print(f"llm.openai_api_base: {self.llm.openai_api_base}")
            print(f"Successfully loaded the llm model")
        
    def ask_one_time(self, question, template=None):
        """ 
        LangChain Expression Language (LCEL)
        https://python.langchain.com/docs/expression_language/
        """
        if not template:
            template = """
            Let's think step by step of the question. 
            Do not generate additional answer besides the direct answer to the question: 
            {question}
            Based on all the thought the final answer becomes:
            """
        
        prompt = PromptTemplate(template=template, input_variables=["question"])
        chain = prompt | self.llm | StrOutputParser() 
        return chain.invoke({"question": question})
    
    def create_conversation_chain(self):
        """needed for the chatbot style conversation"""
        self.conversation = ConversationChain(llm=self.llm)  
    
    def start_conversation(self, question):
        """needed for the chatbot style conversation"""
        return self.conversation.run(question)

