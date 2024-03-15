"""
This is to emulate the topic module in a hypothetical scenario.

eval_result (bool) is generated randomly
need_fq (bool) is generated randomly


<FQ scenario example>

    [CONFIG] retrieve_max_count: 2
    [CONFIG] retrieving 2 additional times while eval_result is False
    retrieve_count: #0 is the initial retrieval from the initial user input
    retrieve_count: #0      query=first user input  (i) parse
    retrieve_count: #0      query=first user input  (ii) understand
    retrieve_count: #0      query=first user input  (iii) start eval...
    retrieve_count: #0      query=first user input  (iii) eval_result: False
    retrieve_count: #0      query=first user input  (iv) current retrieve_count = 0 < retrieve_max_count = 2
    retrieve_count: #0      query=first user input  (iv) changing the prompt for the next retrieving
    retrieve_count: #1      query=first user input  (iv) [RETRIEVE] retrieving again...
    retrieve_count: #1      query=first user input  (iv) successfully retrieved again!
    retrieve_count: #1      query=first user input  (i) parse
    retrieve_count: #1      query=first user input  (ii) understand
    retrieve_count: #1      query=first user input  (iii) start eval...
    retrieve_count: #1      query=first user input  (iii) eval_result: False
    retrieve_count: #1      query=first user input  (iv) current retrieve_count = 1 < retrieve_max_count = 2
    retrieve_count: #1      query=first user input  (iv) changing the prompt for the next retrieving
    retrieve_count: #2      query=first user input  (iv) [RETRIEVE] retrieving again...
    retrieve_count: #2      query=first user input  (iv) successfully retrieved again!
    retrieve_count: #2      query=first user input  (i) parse
    retrieve_count: #2      query=first user input  (ii) understand
    retrieve_count: #2      query=first user input  (iii) start eval...
    retrieve_count: #2      query=first user input  (iii) eval_result: False
    retrieve_count: #2      query=first user input  (v) Done with retrieving since it reached the retrieve max_count

    <FQ section>
    (vi) because eval_result=False and need_fq=True, need to generate FQs
    (vi) generating FQ
    ....
    (vi) generated the FQ
    eval_result from unitrun: False
    need_fq from unitrun: True
    ....
    return the fqs to the upstream
    ....
    FINAL output from the run: fq1: What is your conifg of XXX?


<Downstream example>

    [CONFIG] retrieve_max_count: 2
    [CONFIG] retrieving 2 additional times while eval_result is False
    retrieve_count: #0 is the initial retrieval from the initial user input
    retrieve_count: #0      query=first user input  (i) parse
    retrieve_count: #0      query=first user input  (ii) understand
    retrieve_count: #0      query=first user input  (iii) start eval...
    retrieve_count: #0      query=first user input  (iii) eval_result: True
    retrieve_count: #0      query=first user input  (v) Done with retrieving. eval_result=True
    eval_result from unitrun: True
    need_fq from unitrun: False
    ....
    provide the topic module output to the downstream
    ....

    <DOWNSTREAM section>
    ....[DOWNSTREAM] input eval_result is True, thus try processing further...
    ....[DOWNSTREAM] input content is topic_module_output_JSON
    ....[DOWNSTREAM] input history is [{'query': 'first user input', 'topic_module_output': {'content': 'topic_module_output_JSON'}, 'eval_result': True, 'need_fq': False, 'fqs': []}]
    ....[DOWNSTREAM] generating solutions from the topic_module_output
    ....[DOWNSTREAM] ...
    ....[DOWNSTREAM] successfully generated solutions..
    ....
    FINAL output from the run: generated_sol

"""
from numpy import random


import click



def unitrun(query, history=[]):
    """
    This is the single run

    :param query:
    :return unitrun_output:
    """
    topic_module_output = {}
    retrieve_count = 0
    retrieve_max_count = 2
    eval_result = False
    need_fq = False

    print(f'[CONFIG] retrieve_max_count: {retrieve_max_count}')
    print(f'[CONFIG] retrieving {retrieve_max_count} additional times while eval_result is False')
    print('retrieve_count: #0 is the initial retrieval from the initial user input')

    # (The idea) Do not bother the user unless it is inevitably required...
    while not eval_result and retrieve_count < retrieve_max_count + 1:
        
        # TODO:
        # Handle the history in understanding.

        # parse
        print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(i) parse')

        # understand 
        print(f'retrieve_count: #{retrieve_count}\tquery={query}\t(ii) understand')
        
        # !!! emulate !!!
        topic_module_output['content'] = 'topic_module_output_JSON'
        
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
    

def run_system(query, history=[]):
    """
    """

    # !!! emulate !!!
    query = 'first user input'    

    unitrun_output, history = unitrun(query, history)
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
        return generated_sol
    else:
        if unitrun_output["need_fq"] and len(unitrun_output["fqs"]) >= 1:
            if len(unitrun_output["fqs"]) < 1:
                raise

            print(f'....')
            print(f'return the fqs to the upstream')
            print(f'....')
            assert isinstance(unitrun_output["fqs"], list)
            return '\n'.join(unitrun_output["fqs"])
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
    run_output = run_system(query)
    print(f'FINAL output from the run: {run_output}')
    
    


if __name__ == "__main__":
    main()


