# In the script, it provides an API to consume the regex signatures and query the RAG database to retrieve the solutions 
# Copywrite @Maverick AI 

class RegexSignature():
    def __init__(self, 
                 query_regex_list,
                 elaboration_score=None,
                 num_of_top_list=None,):
        self.query_regex_list = query_regex_list
        self.num_of_top_list = num_of_top_list
        self.elaboration_score=elaboration_score


    def query(self, database_end_point):
        """ used for retrieving the most correlated remediations or configuration setting
        
        Params:
            database_end_point: either the location or API url for RAG database query.
        """
        


    def filtering_and_merge(self, ):
        