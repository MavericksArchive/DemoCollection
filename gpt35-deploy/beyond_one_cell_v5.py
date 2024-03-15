"""
This is to emulate the topic module in a hypothetical scenario.

with a GPT-3.5 LLM instance

eval_result (bool) is generated randomly
need_fq (bool) is generated randomly

"""
import json 


from numpy import random
import click
# from langchain.prompts import PromptTemplate
# from langchain.schema.output_parser import StrOutputParser


def run_unitrun(query, llm, history=[], retrieve_max_count=2):
    """
    This is the single run

    :param query:
    :param llm:
    :param history:
    :return unitrun_output:
    """
    topic_module_output = {}
    retrieve_count = 0
    eval_result = False
    need_fq = False

    print(f'[CONFIG] retrieve_max_count: {retrieve_max_count}')
    print(f'[CONFIG] retrieving {retrieve_max_count} additional times while eval_result is False')
    print('retrieve_count: #0 is the initial retrieval from the initial user input')

    # (The idea) Do not bother the user unless it is inevitably required...
    while not eval_result and retrieve_count < retrieve_max_count + 1:
        
        # TODO:
        # Handle the history in understanding.
        # import pdb; pdb.set_trace()
        
        # parse
        print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(i) parse')

        # understand 
        print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(ii) understand')
                
        res = llm.run_light(query)
        topic_module_output['content'] = json.dumps(res)
        # topic_module_output['content'] = llm.run_light(query)
        # import pdb; pdb.set_trace()
        
        # eval
        print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(iii) start eval...')
       
        # !!! emulate !!!
        eval_result = random.choice([True, False], 1, p=[0.2, 0.8])[0]
        
        print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(iii) eval_result: {eval_result}')

        if retrieve_count == retrieve_max_count:
            break

        if not eval_result:
            print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(iv)'
                  f' current retrieve_count = {retrieve_count} < retrieve_max_count = {retrieve_max_count}')
            
            # retrieve
            print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(iv) changing the prompt for the next retrieving') 
            retrieve_count += 1
            print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(iv) [RETRIEVE] retrieving again...')
            print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(iv) successfully retrieved again!')
            
    if retrieve_count == retrieve_max_count:
        print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(v) Done with retrieving since it reached the retrieve max_count')
    else:
        print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(v) Done with retrieving. eval_result={eval_result}')
       
    # eval again after retrieving 
    # This is the conclusion from the unitrun
    if not eval_result:

        # !!! emulate !!!
        need_fq = random.choice([True, False], 1, p=[1, 0])[0]

    # eval_result is True and we do not need FQ
    if eval_result and not need_fq:
        unitrun_output = {
            'query': query,
            'topic_module_output': topic_module_output,
            'eval_result': eval_result,
            'need_fq': need_fq, 
            'fqs': []
        }
        history.append(unitrun_output)

    # we need need_fq?
    elif not eval_result and need_fq:
        print(f' ')
        print(f'<FQ section>')
        print(f'(vi) because eval_result={eval_result} and need_fq={need_fq}, need to generate FQs')
        print(f'(vi) generating FQ')
        print(f'....')
        print(f'(vi) generated the FQ')

        # !!! emulate !!!
        fqs = ['fq1: What is your conifg of XXX?'] #['fq1', 'fq2', 'fq3']  # should handle multiple fqs
        
        unitrun_output = {
                'query': query,
                'topic_module_output': topic_module_output,
                'eval_result': eval_result,
                'need_fq': need_fq,
                'fqs': fqs 
            }
        
        history.append(unitrun_output)

    else:
        print(f'check this out ...')
        print(f'eval_result: {eval_result}')
        print(f'need_fq: {need_fq}')
        import pdb; pdb.set_trace()
    
    return unitrun_output, history
    

def run_intention(query, llm, history=[], append_conv_hist = False):
    topic_module_output = {}

    # import pdb; pdb.set_trace()
    if append_conv_hist:
        print('.........history........')
        # append conversation history as context
        context = []
        for conv in history:
            if not conv:
                break
            user_query = conv.get('query', None)
            fqs = conv.get('fqs', None)
            sol = conv.get('sol', None)  
            if user_query:  
                context.append(f"USER: {user_query}\n")    
            if fqs:
                context.append(f"SYSTEM: {fqs}\n")
            if sol:
                context.append(f"SYSTEM: {sol}\n")
        
        context = ' '.join(context)
        query = context + f'\nUSER: {query}' if len(history) > 0 else query
    else:
        print('.........NO history........')
        query = query 
    res = llm.run_light(query)
    topic_module_output['content'] = json.dumps(res)
    
    # change the prompt to ask confirmation
    # TODO: 
    
    unitrun_output = {
        'query': query,
        'topic_module_output': topic_module_output,
        'answer': topic_module_output['content'],
        'generated_sol': None,
        'fqs': [],
    }
    history.append(unitrun_output)
            
    return unitrun_output, history


def run_topic_module(query, llm, history=[]):
    """
    :param query:
    :param llm:
    :param history:
    :return :
    """
    CONV_COUNT = len(history)
    max_conv_count = 200
    
    while CONV_COUNT < max_conv_count:
        unitrun_output, history = run_intention(query, llm, history)
        return {
            'answer': unitrun_output['answer'],
            'fqs': unitrun_output['fqs'],
            'generated_sol': unitrun_output['generated_sol'],
            'history': history
        }
            
    unitrun_output, history = run_unitrun(query, llm, history, retrieve_max_count=1)
    
    print(f'eval_result from unitrun: {unitrun_output["eval_result"]}')
    print(f'need_fq from unitrun: {unitrun_output["need_fq"]}')

    if unitrun_output["eval_result"]:
        print(f'....')
        print(f'provide the topic module output to the downstream')
        print(f'....')

        if unitrun_output["need_fq"]:
            raise

        # call downstream task
        print('')
        print(f'<DOWNSTREAM section>')
        generated_sol = call_downstream_task(unitrun_output, history)
        assert isinstance(generated_sol, str)
        
        history = [{k: str(v) for k, v in item.items()} for item in history]
        
        return {
            'fqs': None,
            'generated_sol': generated_sol,
            'history': history
        }
        
    else:
        if unitrun_output["need_fq"] and len(unitrun_output["fqs"]) >= 1:
            if len(unitrun_output["fqs"]) < 1:
                raise

            print(f'....')
            print(f'return the fqs to the upstream')
            print(f'....')
            
            # generating fqs with unitrun_output and history
                        
            assert isinstance(unitrun_output["fqs"], list)
            
            history = [{k: str(v) for k, v in item.items()} for item in history]
            
            return {
                'fqs': '\n'.join(unitrun_output["fqs"]),
                'generated_sol': None,
                'history': history
            }
    
        else:
            print(f'check this out ...')
            print(f'eval_result: {unitrun_output["eval_result"]}')
            print(f'need_fq: {unitrun_output["need_fq"]}')
            print(f'need_fq: {unitrun_output["fqs"]}')
            import pdb; pdb.set_trace()
        

def call_downstream_task(unitrun_output, history):
    """
    Emulating the downstream task

    :param unitrun_output:
    :return generated sol:    
    """
    print(f'....[DOWNSTREAM] input eval_result is {unitrun_output["eval_result"]}, thus try processing further...')
    print(f'....[DOWNSTREAM] input content is {unitrun_output["topic_module_output"]["content"]}')
    print(f'....[DOWNSTREAM] input history is {history}')
    print(f'....[DOWNSTREAM] generating solutions from the topic_module_output')
    print(f'....[DOWNSTREAM] ...')

    # emulate
    generated_sol = 'generated_sol'        
    
    print('....[DOWNSTREAM] successfully generated solutions..')
    print(f'....')
    return generated_sol


@click.command()
@click.option('-q', '--query', default="user_first_intput", help='config')
def main(query):
    """
    Emulates the endpoint. 
    """
    llm = None
    run_output = run_topic_module(query, llm)
    print(f'FINAL output from the run: {run_output}')
    
    


if __name__ == "__main__":
    main()


