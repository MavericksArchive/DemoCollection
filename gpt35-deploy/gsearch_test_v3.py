import time
import json
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

from topic_module_light import TopicModuleLight
from setup import read_yaml
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain.tools import Tool
from langchain.schema import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import WebBaseLoader

from bs4 import BeautifulSoup
import requests

config = 'config/topic_module_config.yaml'

user_input = 'I have 187 devices that show as potentially vulnerable to the PSIRT cisco-sa-iosxe-webui-privesc-j22SaA4z. How can I confirm vulnerability to this PSIRT that allows a remote, unauthenticated attacker to create an account on an affected device with privilege level 15 access and can then use that account to gain control of the affected device?'


# user_input = 'I have 299 devices that show as potentially vulnerable to the PSIRT cisco-sa-secure-client-crlf-W43V4G7. How can I confirm vulnerability?'

# user_input = 'One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. I have noticed that the pubd process is consuming the majority of memory.  Is this a bug?'

config_output = read_yaml(config)
templates = {key: read_yaml(value) for key, value in config_output.get('template', {}).items()}

def extract_entity(tmp, question):
    extract_start_time = time.time()
    template = """
    Imagine three (3) different Cisco Network engineering experts are answering this question. 
    All experts will write down 1 step of their thinking, then share it with the group.
    Then all experts will review each others thoughts and go on to the next step. 
    If any expert realizes they're wrong at any point then they leave. 

    The following observation is relevant to Cisco systems product and their management, configuration, and maintenance.
        
    Based on your knowledge about Cisco products and softwares, please generate the following contents. 
    The answer must contain the following information:
    
    The answer must be a valid JSON objects and formatted as below:
    {{"extracted_entity": <EXTRACTED_ENTITY>}}

    In order to achieve this, each of the Cisco network expert discuss each of the below steps:
        - Step 1. Extract Cisco entity from the input and provide them as a list of Python strings. For example, device name, device hostname, IP address, MAC address, Product ID, Vulnerability ID, Field Notice ID, Defect ID, Product Family Name, and so on. Any entity that is distinguished from the natural language should be extracted here. 
        
    Only return the above as a valid JSON object, following the above JSON structure.
    Do not make up if you do not know the solution. Do not generate any extra words outside of the JSON structure.
    If there exists a question or questions inside the input, pay close attention to those question(s).

    Question: {question}
    Answer:
    """

    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    chain = prompt | tmp.llm | StrOutputParser() 
    entity = chain.invoke({"question": question})
    extract_time_elapsed = time.time() - extract_start_time
    print(f' *** time elapsed [gpt 1st task = extract]: {extract_time_elapsed} seconds')
    return entity


def get_psirt_term(search_term):
    """incomplete... not robust"""
    get_psirt_start_time = time.time()
    if isinstance(search_term, list) and len(search_term) > 0 and isinstance(search_term[0], str):
        try:
            psirt_term = [item for item in search_term if item.upper().find('PSIRT') >= 0 or item.upper().find('VULNERABILIT')  >=  0][0]
        except:
            psirt_term = ' '.join([item for item in search_term if item.startswith('cisco')])
    elif isinstance(search_term, list) and len(search_term) > 0 and isinstance(search_term[0], dict):
        import pdb; pdb.set_trace()
    elif isinstance(search_term, dict):
        psirt_term = ' '.join([f'{k}: {v}' for k, v in search_term.items()])
    elif isinstance(search_term, str):
        psirt_term = ' '.join([item for item in search_term.split(' ') if item.startswith('cisco')])
    else:
        import pdb; pdb.set_trace()

    if isinstance(psirt_term, str) and len(psirt_term):
        pass 
    else:
        print(f'psirt_term: {psirt_term}')
        import pdb;pdb.set_trace()

    psirt_term = ' '.join([item for item in psirt_term.split(' ') if item.startswith('cisco')])
    print(f'    psirt_term: {psirt_term}')
    get_psirt_time_elapsed = time.time() - get_psirt_start_time
    print(f' *** time elapsed [get psirt search term]: {get_psirt_time_elapsed} seconds')
    return psirt_term


def google_search(tmp, psirt_term):
    search_start_time = time.time()
    # search
    try:
        assert load_dotenv(find_dotenv(Path.home()/'doojung'/'.google'/'.env'))  # Load the .env file.
    except AssertionError as errmsg:
        print(f"AssertionError! Env variable did not load!")
        raise

    search = GoogleSearchAPIWrapper()

    def topk_results(query):
        k = 1
        return search.results(query, k)

    tmp.google_search_snip_tool = Tool(
        name="Google Search Snippets",
        description="Search Google for recent results.",
        func=topk_results)

    search_results = tmp.google_search_snip_tool.run(psirt_term, search_params={"cr": "us", "siteSearch": "sec.cloudapps.cisco.com"},)
    print(f'    SEARCH RESULTS: {search_results}')

    try:
        psirt_title = search_results[0]['title']
    except:
        psirt_title = ''

    psirt_link = search_results[0]['link']
    print(f' *** psirt_link: {psirt_link}')
    search_time_elapsed = time.time() - search_start_time
    print(f' *** time elapsed [google search]: {search_time_elapsed} seconds')
    return psirt_title, psirt_link


def load_parse_web_doc(psirt_link):
    parse_start_time = time.time()

    # load the web document
    loader = WebBaseLoader(psirt_link)
    data = loader.load()

    context = data[0].metadata.get('description')
    page_content = data[0].page_content.replace('\n', '')
    page_content = ' '.join(page_content.split())
    context = context + '' +  page_content[:3000 - len(context)]
    # print(f' *** context: {context}')

    # parsing the web document
    r = requests.get(psirt_link)
    soup = BeautifulSoup(r.text, "html.parser")
    det_vul = soup.find_all("div", id="vulnerableproducts")
    if len(det_vul) > 0:
        det_vul = det_vul[0].get_text()
    
    recom = soup.find_all("div", id="recommendationsfield")
    if len(recom) > 0:
        recom = recom[0].get_text()
    else:
        print(f'!!! WARNING !!! parsing recom...')
        print(f'!!! len(recom)=={len(recom)} !!! ')
        recom = None

    fixed = soup.find_all("div", id="fixedsoftfield")
    if len(fixed) > 0:
        fixed = fixed[0].get_text()
    else:
        print(f'!!! WARNING !!! parsing fixed...')
        print(f'!!! len(fixed)=={len(fixed)} !!! ')
        fixed = None

    context = f"Description: {context}. "
    if det_vul:
        context += f"How to detect: {det_vul}. "
    if recom:
        context += f"Recommendations: {recom} "
    if fixed:
        context += f"Fixed Software: {fixed}"
    
    parse_time_elapsed = time.time() - parse_start_time
    print(f' *** time elapsed [parse]: {parse_time_elapsed} seconds')
    return context


def ask(tmp, topic_module_output, context):
    gpt2nd_ask_start_time = time.time()

    # print(f'EXTRACTED CONTEXT: {context}')

    template = """
    Use the following pieces of Context to answer the Question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Do not generate additional answer besides the direct answer to the question: 

    1. Let's think step by step. Provide the generated thoughts. 
    2. Cross-reference the answer with Context to ensure accuracy.

    Context: {context}
    Question: {question}
    """

    question = """
    Please summarize from the provided context while keeping as much as technical details in the summary. 
    Additionally, extract as many as following information from the provided context and compose a new sentence. 
    The description, bug ID, CVE ID, CVSS score, severity, summary, how to determine the vulnerability, recommendation, and solutions. 
    
    You must include any software version, code snippet, commands to run, and the technical details mentioned in the context you can find and include in the final output."""

    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    chain = prompt | tmp.llm | StrOutputParser() 
    knowledge = chain.invoke({"context": context, "question": question})
    topic_module_output['situation'] = knowledge
    
    print(f'    KNOWLEDGE: {knowledge}')
    response = knowledge
    
    gpt2nd_time_elapsed = time.time() - gpt2nd_ask_start_time
    print(f' *** time elapsed [gpt2nd]: {gpt2nd_time_elapsed} seconds')
    return response


def ask_with_solution(tmp, topic_module_output, context):
    gpt2nd_ask_start_time = time.time()

    template = """
    Imagine three (3) different Cisco Network engineering experts are answering this question. 
    All experts will write down 1 step of their thinking, then share it with the group.
    Then all experts will review each others thoughts and go on to the next step. 
    If any expert realizes they're wrong at any point then they leave. 

    The following observation is relevant to Cisco systems product and their management, configuration, and maintenance.
        
    Based on your knowledge and the context provided about Cisco products and softwares, please generate the following contents. 
    The answer must contain the following information:
      - 1. KNOWLEDGE: Please summarize from the provided context while keeping as much as technical details in the summary and provide them as a list of Python strings. The output must include as many as following information extracted from the provided context and compose a new sentence. The description, bug ID, CVE ID, CVSS score, severity, summary, how to determine the vulnerability, recommendation, and solutions. You must include any software version, code snippet, commands to run, and the technical details mentioned in the context you can find and include in the final output.
      - 2. SOLUTIONS: In three bullet points, suggest a list of potential solutions from the identified problem and provide them as a list of Python strings. 

    The answer must be a valid JSON objects and formatted as below:
    {{"knowledge": <KNOWLEDGE>, "solutions": <SOLUTIONS>}}

    In order to achieve this, each of the Cisco network expert discuss each of the below steps:
        - Step 1. In bullet points, write a list of items in your KNOWLEDGE and provide them as a list of Python strings. Include as much technical details as you can extract from the context. 
        - Step 2. In bullet points, suggest a list of solutions from the identified problem and provide them as a list of Python strings.. 

    Only return the above as a valid JSON object, following the above JSON structure.
    Do not make up if you do not know the solution. Do not generate any extra words outside of the JSON structure.
    If there exists a question or questions inside the input, pay close attention to those question(s).

    Context: {context}
    Question: {question}
    Answer:
    """

# (a)  You must include the following as one of your solutions: add software upgrade, fixed release, or similar to the solution.
# (a) You must include the following as one of your solutions: add software upgrade, fixed release, or similar to the solution.
#     - Step 2. In bullet points, suggest a list of solutions from the identified problem and provide them as a list of Python strings.. The last bullet point should alwyas include the following as one of your solutions: integrate the remediation action into their change management process, such as creating a ServiceNow incident ticket. 
# The last bullet point should alwyas include the following as one of your solutions: add software upgrade, fixed release, or similar to the solution.

    # renewing experimenting..
    
    renew_time_kpi = time.time()
    renew_required = tmp._renew_llm_token()
    if renew_required:
        print(f'--------' * 20)
        print(f'Renewing LLM ... ')
        tmp.cisco_chat_ai.load_llm_model()
        tmp.llm = tmp.cisco_chat_ai.llm
        print(f'Successfully renewed LLM')
        renew_time_kpi_elapsed = time.time() - renew_time_kpi
        print(f'Time passed creating new auth token and renewing LLM: {renew_time_kpi_elapsed} seconds')
        print(f'--------' * 20)
    # renewing experimenting..
    
    def invoking(template, context, user_input):
        # from json.decoder import JSONDecodeError
        # raise JSONDecodeError('Custom error', doc='my doc', pos=8888)
        # raise Exception('Customer error')
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])
        chain = prompt | tmp.llm | StrOutputParser() 
        results = chain.invoke({"context": context, "question": user_input})
        json_result = json.loads(results)
        return json_result
    
    # retry 
    no_of_trial, GPT_RETRY_MAX = 0, 10
    while True and (no_of_trial < GPT_RETRY_MAX):
        try:
            no_of_trial += 1
            json_result = invoking(template, context, user_input)
        except Exception as errmsg:
            print(f'GPT-3.5 error. Trying again... Retry #{no_of_trial}')
            time.sleep(3)
            continue
        break
    
    # prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    # chain = prompt | tmp.llm | StrOutputParser() 
    # response = chain.invoke({"context": context, "question": user_input})
    
    gpt2nd_time_elapsed = time.time() - gpt2nd_ask_start_time
    print(f' *** time elapsed [gpt 2nd task = solution gen]: {gpt2nd_time_elapsed} seconds')
    return json_result

def main():
    
    main_start_time = time.time()
    
    # instantiate
    tmp = TopicModuleLight(config_output, templates)
    
    # topic module - 1st
    # topic_module_output = tmp.run_light(user_input)
    # print(f'type(topic_module_output): {type(topic_module_output)}')

    # find the search term
    # mock.
    # topic_module_oup
    
    extracted_entity = extract_entity(tmp, user_input)
    topic_module_output = {'extracted_entity': json.loads(extracted_entity)['extracted_entity']}
    search_term = topic_module_output['extracted_entity']
    psirt_term = get_psirt_term(search_term)
    
    # do the google seaerch 
    psirt_title, psirt_link = google_search(tmp, psirt_term)
    
    # get the search result
    context = load_parse_web_doc(psirt_link)

    # ask GPT-35 
    # response = ask(tmp, topic_module_output, context)
    json_result = ask_with_solution(tmp, topic_module_output, context)
    # import pdb; pdb.set_trace()
    # topic_module_output['knowledge'] = json.loads(response)['knowledge']
    # topic_module_output['solutions'] = json.loads(response)['solutions']
    topic_module_output['knowledge'] = json_result['knowledge']
    topic_module_output['solutions'] = json_result['solutions']

    print(f'=====' * 20)
    for key, value in topic_module_output.items():
        print(f' ')
        print(f'* {key}: {value}')
        print(f' ')

    print(f'=====' * 20)
    print('Done')
    main_elapsed_time = time.time() - main_start_time
    print(f'Time elapsed: {main_elapsed_time}')


if __name__ == "__main__":
    main()
