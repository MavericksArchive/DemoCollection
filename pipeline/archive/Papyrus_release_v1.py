import os
import sys 
import click
import logging 

# test end
from langchain.schema.document import Document

sys.path.append('..')
from utils.setup import read_yaml, setup_logging
from Topic_Embedding.topic_module import TopicModule
from papyrus.papyrus_generation import PapyrusGeneration


def run_topic_module(config, templates, user_input):
    # run    
    topic = TopicModule(config, templates)   # <- yes you need to do 
    topic_module_output = topic.run(user_input)          # <-- yes, the user input is the user text "xxxx"
    
    # inspect the output
    logging.info('Returning the output of the topic module!')    
    return {
        'topic_module_class': topic,
        'topic_module_output': topic_module_output}


def run_papyrus_module(config, 
                       template, 
                       topic_module_class,
                       topic_module_input):
    
    # initialization
    papyrus_module_class = PapyrusGeneration(config,
                                             template,
                                             topic_module_class)
    
    regex_signature, solution = papyrus_module_class.test_solution_gen(topic_module_input[0],  
                                                                       topic_module_input[1]) 
    
    # retrieve the solution from RAG database 
    papyrus_module_retrived = papyrus_module_class.retrieve(regex_signature)

    return {
           'papyrus_module_retrived': papyrus_module_retrived,
           'papyrus_module_solution': solution['solution']
    }

@click.command()
@click.option('-c', '--config', default='../cisco_chat_experiments/configs/topic_module_config.yaml', help='config')
@click.option('-t', '--templates', default='../cisco_chat_experiments/prompt_templates/topic_module_templates.yaml', help='config')
def main(config, templates, user_input=None):
    """
    This is to show how to use this class.    
    """
    log_filename = setup_logging(log_name = 'topic_module')
    logging.info('As of 02/14/2024')
    
    config = read_yaml(os.path.abspath(config))     # <-- no change
    templates = read_yaml(os.path.abspath(templates))     # <-- no change

    # get the data
    # user_input = get_test_examples()    # <- yes, you need to do. Currently getting one example  
    user_input = """Greetings and salutations. I was given a project to take over, but one of the switches is in limbo right now. \
        They want the default IOS, 17.03.04, to be replaced with an older IOS, 16.12.03a. \
        Normally I would just copy the second IOS to flash and select which one to boot with. \
        Unfortunately, the flash size is too small to hold both IOSes at the same time. \
        I'm working with a Catalyst 9200-49 PoE+ The two IOSes are: cat9k_lite_iosxe.17.03.04.SPA.bin and cat9k_iosxe.16.12.03a.SPA.bin. \
        My idea is to boot with IOS 16 from the tftp server, delete the files for IOS 17 to make room for IOS 16, and then install it. \
        I tried numerous times to talk them out of downgrading and instead to just upgrade the switches already in the field to IOS 17, \
        but they don't want to take down the whole network to do this. This seems long-winded and time-consuming. Is there a quicker way to do this? """

    # user_input = """ i signed in to a new ISR 1100 series router and get this message after the configuration finished installing and prompted to there a new password  %Cisco-SDWAN-RP_0-CFGMGR-4-WARN-300005: R0/0: CFGMGR: New admin password not set yet, waiting for daemons to read initial config."""
    
    
    ##################################################################
    #### Topic module
    ##################################################################
    output = run_topic_module(config, templates, user_input)
    topic_module_class = output['topic_module_class']
    topic_module_output = output['topic_module_output']

    
    ##################################################################
    #### CALL BI/CE sentence transformer query
    ##################################################################
    query = ""
    output_keys = list(topic_module_output.keys())
    # ['user_input_desc', 'user_input_code', 'goal', 'main_question', 'code_interpretation', 'code_line_by_line_results_str', 'eval', 'eval_reason']
    target_keys = output_keys
    for key in target_keys:
        if isinstance(topic_module_output.get(key, ""),str) and len(topic_module_output.get(key, ""))>0:
            query+=topic_module_output.get(key, "")+"\n"

    logging.info(f"bi/ce-encoder query input: {query}")
    unique_docs = topic_module_class.test_fine_tuned_bi_ce_encoder(query)
    for idx, d in enumerate(unique_docs):
        logging.info(f"bi/ce-encoder output {idx} - {d.metadata['score']}|{d.metadata['cross-score']}: {d.metadata['url']}, {d.metadata['title']}")

    
    ##################################################################
    #### Papyrus Module
    ##################################################################

    logging.info(f"user intention for papyrus inputs includes: {topic_module_output}")
    
    papyrus_output = run_papyrus_module(config,  
                                        templates, 
                                        topic_module_class, 
                                        (topic_module_output, unique_docs))
    logging.info(f"retrieved solution from RAG database: {papyrus_output['papyrus_module_retrived']}")
    logging.info(f"generated solution from papyrus: {papyrus_output['papyrus_module_solution']} ")
    
if __name__ == "__main__":
    main()