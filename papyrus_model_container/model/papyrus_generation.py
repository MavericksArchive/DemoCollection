import logging
import os
from model.papyrus_model import PapyrusModel


os.environ['CUDA_VISIBLE_DEVICES'] = '0'

class PapyrusGeneration():
      def __init__(self,
                   config,
                   output_template,
                   generation_config=None,
                   ):
          """
          Params: 
             generation_config: the configuration used for LLMs generation. The key fields include
                               do_sample, max_new_tokens, temperature, top_p, repetition_penalty
          """
          self.config = config
          self.output_template = output_template
          self.generation_config=generation_config
          # self.topic_module_class = topic_module_class

          # get the bice model 
          # if self.config['kb']['bice']:
          #      self.bice = self.topic_module_class.bice_model

          # load the papyrusModel
          adapter_path = os.path.abspath(self.config['papyrus']['model_path'])
          basemodel_path = os.path.abspath(self.config['papyrus']['base_model_path'])
          self.load_model_config(adapter_path,
                           base_model_path=basemodel_path)

      def load_model_config(self, 
                      lora_model_path, 
                      base_model_path,
                       model_merged=False):
           logging.info('loading the papyrus model config!')
           self.papyrus = PapyrusModel(lora_model_path,
                                       base_model_path,
                                       model_merged)
           logging.info('successfully initialized the papyrus model config!')     

      def _solution_generation(self, 
                               model, 
                               tokenizer, 
                               inputs, 
                               generation_indication):
           """
             wrap up the inputs components and focus on generate regex signature for 
             pattern identification

             Params:
             - inputs: the details including the observation patterns or problem description, 
                       string type. 
           """

           solutions = self.papyrus.generation(
                                               model,
                                               tokenizer,
                                               inputs, 
                                               generation_indication=generation_indication,
                                               generation_config= self.generation_config)
           return solutions

      def _prepare_instructions(self, 
                                input_desc, 
                                instruction_indicator,
                                solution_flag=None,
                                rag_feature=None):
          """ use different templates to formlize the prompts for different instruction indicator

          Params:
            input_desc: the translated user input to represent user intention. String from topic module.
            instruction_indicator: the indicator used to refer to the regex signature, solution, solution with
                                   code snippet tasks. 
            rag_feature: the feature/item extracted from RAG database for context or few-shot learning. 
          """
          if instruction_indicator != 'solution_with_code':
               inputs = []

               # process the number of devices
               import re
               import random
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
                    # # if isinstance(context_info, list):
                    #    for sub_context in context_info:
                    #           if len(sub_context):
                    #                sample = init_+ input_desc + ' ' + sub_context + '\n\n'
                    #           else:
                    #                sample = init_ + input_desc + '\n\n'
                    #           sample += instruction_prompt['Rule'] + '\n\n' + instruction_prompt['RuleKey'] + '\n'
                    #           inputs.append(sample)
                    # else:
                    #     sample = init_+ input_desc + '\n\n'
                    #     sample += instruction_prompt['Rule'] + '\n\n' + instruction_prompt['RuleKey'] + '\n'
                    #     inputs.append(sample)
                         

                    # inputs.append(init_)
    
          elif instruction_indicator == 'solution_with_code':
               pass

          return inputs
      
      def _instruction_prompts(self, 
                              input_desc, 
                              generation_indication,
                              solution_flag=False,
                              rag_feature=None):
          """ Wrap the raw inputs with instructions according to user intention. 

          Params:
              input_desc: the raw user inputs. 
              rag_feature: the queried knowledgebase feature/item descriptions. These rag features 
                           are used as either few-shot learning (for instance, in gnosis-style dataset, 
                           the extracted item describes how to solve the problem, and the regex signature.) or
                           context info (for instance, the production-manual style dataset, when user raises the
                           configuration optimization request, the extracted feature description are context.)
          """
          # get the generation indication
          # generation_intention = self.bice.sentence_transformer_similarity(input_desc, 
          #                                              ['pattern_identification', 
          #                                              'workaround_or_solution',
          #                                              'solution_with_exectuable_code_snippets'])
          self.generation_indication =  self.config['generation_task'][generation_indication]                                          
          logging.info(f'the intention of user is to get {self.generation_indication}')

          instructed_prompt = self._prepare_instructions(input_desc, 
                                                         self.generation_indication, 
                                                         solution_flag=solution_flag,
                                                         rag_feature=rag_feature)

          return instructed_prompt

      def test_solution_gen(self, 
                            model,
                            tokenizer,
                            topic_module_output,
                            generation_indication,
                            unique_docs=None,
                            interpreation=None):
          """
               # generate outcome,
               # the form of the outcome is determined by the user's intention
               # for instance, if user is trying to identify the patterns for diagnosis, 
               # the outcome is with regex format; if user is trying to get workaround, the outcome
               # is with solutions and proposals; if user is trying to get executable code snippets 
               # for configuration from CLI, the outcome is with code snippets.
               # if none of them are specified in user's input, then all possible cases are considered
          
          Params:
             topic_module_output: a dictionary from topic module, including all key fields.
             output_keys: the keys in topic_module_output
             unique_docs: the extracted items/features from RAG database.

          """
          # utilize all the information to generate regex 
          # solution 
          # if possible, generate solution with code_snippet    
          

          # get useful fields from the topic module
          # user_goal = topic_module_output['goal']
          user_desc = topic_module_output['user_input_desc']
          # user_question = topic_module_output['main_question']
          solution_flag = topic_module_output['run_papyrus_solution']

          # get useful document description from embedding module
          # here only use the top choice
          # top_description = unique_docs[0]

          # RAG description 
          # rag_description = top_description.page_content
          rag_description = None

          # logging.info(f"RAG feature description: {rag_description}")

          # identify the patterns, if CLI command output exists in the input/ code in the 
          # code and problem 
          prompt_user = self._instruction_prompts(user_desc, 
                                                  generation_indication,
                                                  solution_flag=solution_flag,
                                                  rag_feature=rag_description)# RAG items/features
          

          # logging.info(f"papyrus input prompts {prompt_user}")
          outcome = self._solution_generation(model, 
                                              tokenizer,
                                              prompt_user,
                                              self.generation_indication)

          # regex_signature = None
          # if 'regex' in self.generation_indication:
          #      regex_signature = outcome

          # code splitting


          return outcome
          
           
           
           
           
