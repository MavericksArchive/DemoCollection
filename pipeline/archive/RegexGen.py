# In the script, it provides an API to consume the user descriptions and generate regex signatures 
# Copywrite @Maverick AI 


class RegexGen():
    def __init__(self,
                 model,
                 model_config,
                 tokenizer,
                 generation_config,
                 ):
        self.model = model
        self.model_config=model_config
        self.generation_config=generation_config
        self.tokenizer = tokenizer


    def get_regex(self, description):
        tokenized_description = self.tokenizer(description, self.model_config)
        regex_lists = self.model(tokenized_description)
        regex_decoded = self.tokenizer(regex_lists)
        return regex_decoded

    def get_regex_few_shot(self, rag_input_samples):
        """ utilizing few shot learning to enhance the outputs
        """
        pass



    def get_regex_reinforce(self, user_feedback, context=None, reward=None):
        """Add context info & user feedback to reinforce the regex generator model's output

        Params: 
            user_feedback: either a satisfaction score or user description regarding the validation results
            context: info regarding the device/software info used for filtering out irrelevant solution.
            reward: the gain on each update 
        """
        pass