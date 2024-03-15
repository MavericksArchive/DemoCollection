import time
start_time = time.time()


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
tmp = TopicModuleLight(config_output, templates)


# topic module 
topic_module_output = tmp.run_light(user_input)
print(f'type(topic_module_output): {type(topic_module_output)}')
search_term = topic_module_output['extracted_entity']

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
print(f' *** psirt_term: {psirt_term}')

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
print(f' *** search_results: {search_results}')

import pdb;pdb.set_trace()

try:
    psirt_title = search_results[0]['title']
except:
    psirt_title = ''

psirt_link = search_results[0]['link']
print(f' *** psirt_link: {psirt_link}')

loader = WebBaseLoader(psirt_link)
data = loader.load()

context = data[0].metadata.get('description')
page_content = data[0].page_content.replace('\n', '')
page_content = ' '.join(page_content.split())
context = context + '' +  page_content[:3000 - len(context)]
# print(f' *** context: {context}')

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
    
if recom:
    context = f"Description: {context}. How to detect: {det_vul}.  Recommendations: {recom}"
else:
    context = f"Description: {context}. How to detect: {det_vul}"
    
question = """
Please summarize the provided context. Additionally, extract as many as following information from the provided context and compose a new sentence. 
The description, bug ID, CVE ID, CVSS score, severity, summary, how to detect, recommendation, and solutions."""

print(f'extract context: {context}')

template = """
Use the following pieces of Context to answer the Question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Do not generate additional answer besides the direct answer to the question: 

1. Let's think step by step. Provide the generated thoughts. 
2. Cross-reference the answer with Context to ensure accuracy.

Context: {context}
Question: {question}
"""

prompt = PromptTemplate(template=template, input_variables=["context", "question"])
chain = prompt | tmp.llm | StrOutputParser() 
knowledge = chain.invoke({"context": context, "question": question})
topic_module_output['situation'] = f"{topic_module_output['situation']}. {knowledge}"


template = """
Use the following pieces of Context to answer the Question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Do not generate additional answer besides the direct answer to the question: 

1. Let's think step by step. Provide the generated thoughts. 
2. Cross-reference the answer with Context to ensure accuracy.

Context: {context}
Question: {question}
"""
question = f"""
Revise the context provided using the provided context. 
Pay close attention to how to detect and what was recommended. 
Solution: {topic_module_output['solutions']}"""

prompt = PromptTemplate(template=template, input_variables=["context", "question"])
chain = prompt | tmp.llm | StrOutputParser() 
topic_module_output['solutions'] = chain.invoke({"context": topic_module_output['situation'], "question": question})

print(f'=====' * 20)
for key, value in topic_module_output.items():
    print(f'{key}: {value}')

print(f'=====' * 20)
print('Done')
elapsed_time = time.time() - start_time
print(f'Time elapsed: {elapsed_time}')

"""
"""