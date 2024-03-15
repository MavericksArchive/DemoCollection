"""
This is to emulate the topic module in a hypothetical scenario.

eval_result (bool) is generated randomly
need_fq (bool) is generated randomly
"""
from numpy import random


import click



def unit_run(query):
    """
    This is the single run

    :param query:
    :return eval_result:
    :return need_fq:    
    """
    retrieve_count = 0
    retrieve_max_count = 2
    eval_result = False
    need_fq = False
    
    # (The idea) Do not bother the user unless it is inevitably required...
    while not eval_result and retrieve_count < retrieve_max_count:
        # parse
        print(f'ret_count: #{retrieve_count}\tquery={query}\t(i) parse')

        # understand 
        print(f'ret_count: #{retrieve_count}\tquery={query}\t(ii) understand')

        # eval
        print(f'ret_count: #{retrieve_count}\tquery={query}\t(iii) start eval...')
        eval_result = random.choice([True, False], 1, p=[0.2, 0.8])[0]
        print(f'ret_count: #{retrieve_count}\tquery={query}\t(iii) eval_result: {eval_result}')

        if not eval_result:
            print(f'ret_count: #{retrieve_count}\tquery={query}\t(iv) current retrieve_count = {retrieve_count}')
            
            # retrieve
            print(f'ret_count: #{retrieve_count}\tquery={query}\t(iv) changing the prompt for the next retrieving') 
            print(f'ret_count: #{retrieve_count}\tquery={query}\t(iv) retrieving again...')
            print(f'ret_count: #{retrieve_count}\tquery={query}\t(iv) successfully retrieved again! Let us parse/understand/eval again')
            retrieve_count += 1
    
    if retrieve_count == retrieve_max_count:
        print(f'ret_count: #{retrieve_count}\t(v) Done with retrieving since it reached the retrieve max_count')
    else:
        print(f'ret_count: #{retrieve_count}\t(v) Done with retrieving')
       
    # eval again after retrieving 
    # This is the conclusion from the unit_run
    if not eval_result:
        need_fq = random.choice([True, False], 1, p=[1, 0])[0]
    return eval_result, need_fq
    

    
def run(query):
    """
    
    
    """
    fq_count = 0
    fq_max_count = 1

    query = 'first user input'    
    eval_result, need_fq = unit_run(query)
    print(f'eval_result from unit_run: {eval_result}')
    print(f'need_fq from unit_run: {need_fq}')

    # eval_result is True and we do not need FQ
    if eval_result and not need_fq:
        return {
            'eval_result': eval_result,
            'need_fq': need_fq 
        }

    # we need need_fq?
    while not eval_result and need_fq and fq_count < fq_max_count:
        fq_count += 1
        print(f'fq_count: #{fq_count}\t(vi) generating FQ')
        print(f'fq_count: #{fq_count}\t(vi) asking FQ')
        
        ## hmmm...
        # how to we get this from the user in the real scenario?
        # maybe we should stop here and return.

        query = input('Here is my follow up question. XXXX? Please answer:')

        print(f'fq_count: #{fq_count}\t(vi) user_input={query}')
        print(f'fq_count: #{fq_count}\t(vi) running the iteration (unit_run)...')
        eval_result, need_fq = unit_run(query)
        print(f'fq_count: #{fq_count}\t(vi) eval_result from unit_run: {eval_result}')
        print(f'fq_count: #{fq_count}\t(vi) need_fq from unit_run: {need_fq}')

    if fq_count == fq_max_count:
        print(f'fq_count: #{fq_count}\t(vi) Done with FQ since it reached the fq max_count.')
    
    print('fq_count: #{fq_count}\t(vi) Done with FQ')

    # final eval
    return {
            'eval_result': eval_result,
            'need_fq': need_fq 
        }


@click.command()
@click.option('-q', '--query', default="user_first_intput", help='config')
def main(query):
    """
    Emulates the endpoint
    
    """
    output = run(query)
    print(f'FINAL eval_result from main: {output["eval_result"]}')
    print(f'FINAL need_fq from main: {output["need_fq"]}')
    print('FINAL beyond one cell finished')
    
    # TODO:
    # what happens the FINAL eval_result is False? 



if __name__ == "__main__":
    main()


