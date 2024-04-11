import os
import re
import logging
from typing import List 

from model.papyrus_model import PapyrusModel


os.environ['CUDA_VISIBLE_DEVICES'] = '0'


class PapyrusGeneration():
    def __init__(
        self,
        config,
        output_template,
        generation_config=None,
        ):
        """
        :param config:
        :param output_template:
        :param generation_config: the configuration used for LLMs generation. The key fields include
            do_sample, max_new_tokens, temperature, top_p, repetition_penalty
        """
        self.config = config
        self.output_template = output_template
        self.generation_config=generation_config

        # load the papyrusModel
        adapter_path = os.path.abspath(self.config['papyrus']['model_path'])
        base_model_path = os.path.abspath(self.config['papyrus']['base_model_path'])
        self.load_model_config(adapter_path, base_model_path=base_model_path)

    def load_model_config(
        self, 
        lora_model_path, 
        base_model_path,
        model_merged=False):
        """
        :param lora_model_path:
        :param base_model_path:
        :param model_merged:
        """
        logging.info('loading the papyrus model config!')
        self.papyrus = PapyrusModel(lora_model_path, base_model_path, model_merged)
        logging.info('successfully initialized the papyrus model config!')     

    def _solution_generation(self, model, tokenizer, inputs, generation_indication):
        """
        Wrap up the inputs components and focus on generate regex signature for 
        pattern identification

        :param model:
        :param tokenizer:
        :param inputs: the details including the observation patterns or problem description, 
            string type. 
        :param generation_indication:
        :return solutions:
        """
        solutions = self.papyrus.generate(
            model,
            tokenizer,
            inputs, 
            generation_indication=generation_indication,
            generation_config=self.generation_config)
        return solutions

    def _prepare_instructions(
        self, input_desc, instruction_indicator, 
        solution_flag=None, rag_feature=None) -> List:
        """ 
        Use different templates to formalize the prompts for different instruction indicator

        :param input_desc: the translated user input to represent user intention. String from topic module.
        :param instruction_indicator: the indicator used to refer to the regex signature, solution, solution with
            code snippet tasks. 
        :param solution_flag:
        :param rag_feature: the feature/item extracted from RAG database for context or few-shot learning. 
        :return inputs:
        """
        inputs = []
        if instruction_indicator != 'solution_with_code':
            # process the number of devices
            input_desc = re.sub(r'\b\d+\b', '187', input_desc)

            # populate the prompt with the regex-specific instructions
            context_keys = list(self.output_template['papyrus']['context_prompt'].keys())
            selected_key = None
            for sub_key in context_keys:
                if sub_key in input_desc:
                    selected_key = sub_key
                    break
            task_list = ['regex'] if not solution_flag else ['regex', 'solution']
            for sub_task in task_list:
                instruction_prompt = self.output_template['papyrus'][sub_task]
                init_ = instruction_prompt['Intro'] + '\n\n' + instruction_prompt['IntroKey'] + '\n' 
                
                if selected_key:
                    if sub_task in self.output_template['papyrus']['context_prompt'][selected_key]:
                        context_info = self.output_template['papyrus']['context_prompt'][selected_key][sub_task]
                        sample = init_ + input_desc + ' ' + context_info + '\n\n' if len(context_info) else  init_ + input_desc + '\n\n'
                    else:
                        sample = init_ + input_desc + '\n\n'
                else:
                    sample = init_ + input_desc +  '\n\n'

                sample += instruction_prompt['Rule'] + '\n\n' + instruction_prompt['RuleKey'] + '\n'
                inputs.append(sample)  

        elif instruction_indicator == 'solution_with_code':
            raise NotImplementedError

        return inputs
    
    def _instruction_prompts(
        self, 
        input_desc, 
        generation_indication,
        solution_flag=False,
        rag_feature=None):
        """
        Wrap the raw inputs with instructions according to user intention. 

        :param input_desc: the raw user inputs. 
        :param generation_indication: 
        :param solution_flag:
        :param rag_feature: 
            The queried knowledge base feature/item descriptions. These rag features 
            are used as either few-shot learning (for instance, in gnosis-style dataset, 
            the extracted item describes how to solve the problem, and the regex signature.) or
            context info (for instance, the production-manual style dataset, when user raises the
            configuration optimization request, the extracted feature description are context.)
        :return prompted_user_input:
        """
        # get the generation indication
        self.generation_indication = self.config['generation_task'][generation_indication]                                          
        logging.info(f'the intention of user is to get {self.generation_indication}')

        prompted_user_input = self._prepare_instructions(
            input_desc, 
            self.generation_indication, 
            solution_flag=solution_flag,
            rag_feature=rag_feature)

        return prompted_user_input

    def test_solution_gen(
        self, 
        model,
        tokenizer,
        intention_module_output,
        generation_indication,
        unique_docs=None,
        interpretation=None):
        """
        Utilize all the information to generate regex/solution.
        
        The form of the outcome is determined by the user's intention.
        for instance, if user is trying to identify the patterns for diagnosis, the outcome 
        is with regex format; if user is trying to get workaround, the outcome is with 
        solutions and proposals; if user is trying to get executable code snippets for 
        configuration from CLI, the outcome is with code snippets.
        If none of them are specified in user's input, then all possible cases are considered
        
        :param model:
        :param tokenizer:
        :param intention_module_output: a dictionary from intention module, including all key fields.
        :param generation_indication: E.g., 'pattern_identification', ...
        :param unique_docs: the extracted items/features from RAG database. Not used.
        :param interpretation: User intention interpretation output. Not used.
        :return outcome:
        """
        # get useful fields from the intention module
        user_desc = intention_module_output['user_input_desc']
        solution_flag = intention_module_output['run_papyrus_solution']

        # get useful document description from embedding module
        # here only use the top choice
        # top_description = unique_docs[0]

        # RAG description 
        rag_description = None

        # Generate the instruction        
        prompted_user_input = self._instruction_prompts(
            user_desc, 
            generation_indication,
            solution_flag=solution_flag,
            rag_feature=rag_description) # RAG items/features

        # Generation the regex/solution
        outcome = self._solution_generation(
            model, 
            tokenizer,
            prompted_user_input,
            self.generation_indication)

        return outcome
          
           
           
           
           
