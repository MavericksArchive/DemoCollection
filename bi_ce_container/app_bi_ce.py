"""
Run the bi-encoder and cross-encoder for a given query.

The bi-encoder and cross-encoder are fine-tuned on GNOSIS and SR data.
 - Given a search query, we first use a retrieval system that retrieves a large 
    list of e.g. 100 possible hits which are potentially relevant for the query.
 - However, the retrieval system might retrieve documents that are not that relevant 
     for the search query. Hence, in a second stage, we use a re-ranker based on a 
     cross-encoder that scores the relevancy of all candidates for the given search query.
 - The output will be a ranked list of hits we can present to the user.
"""
import re
import time 
import json 


import numpy as np
import torch 
from flask import Flask, request, jsonify
from langchain.schema.document import Document
from sentence_transformers import util


from my_bi_model import MyBIModel
from my_ce_model import MyCEModel
from bi_ce_utils import load_config, ciscocom_merged_data_reader


app = Flask(__name__)
config = load_config()

print(f"Load config:")
print(config)

returned_top_k = config['return_top_k']
candidate_num = config['candidate_num']
ciscocom_data_file = config['ciscocom_data_file']
bi_model_name_or_path = config['bi_model_name_or_path']
ce_model_name_or_path = config['ce_model_name_or_path']
device = config['device']
embed_file_path = config['embed_file_path']

query_list, text_list = ciscocom_merged_data_reader(file_path=ciscocom_data_file)
print("BICE_Model __init__: Loaded the title and context list !!!!")

url_list=[]

re_pattern = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
for t in query_list:
    url_list.append(re.findall(re_pattern, t)[0])
print("BICE_Model __init__: Loaded the URL list !!!!")

bi_model = MyBIModel(
    bi_model_name_or_path, bnb_config=None, train_type="margin", device=device).to(device)
print("BICE_Model __init__: Loaded the BI model !!!!")

ce_model = MyCEModel(ce_model_name_or_path, num_labels=1, device=device).to(device)
print("BICE_Model __init__: Loaded the CE model !!!!")

embed_file_path = embed_file_path
print(f"BICE_Model __init__: Read Bi-Embedding from disk {embed_file_path}")

topic_embedding_tensor = torch.load(embed_file_path)
print("BICE_Model __init__: shape of embedding ", topic_embedding_tensor.shape)


def get_cluster_list(corpus_id, cluster_list):
    """
    Get the list of clusters
    
    :param corpus_id:
    :param cluster_list:
    :return l_id:
    """
    for l_id, l in enumerate(cluster_list):
         if corpus_id in l:
            return l_id
    return None


@app.route('/query', methods=['POST'])
def sbert_query():
    """
    Run the bi-encoder/cross-encoder query against the question.
    """
    print(request)
    data = request.get_json(force=True)
    print(data)
    question = data['question']

    if topic_embedding_tensor.shape[0] != len(text_list):
        # print("Please guarantee the embedding and source documents have the same size. ")
        return jsonify({
                "message": "Please guarantee the embedding and source documents have the same size. "
        }), 403
    
    # bi-encoder
    question_embedding = bi_model.encode([question], show_bar=False)
    question_embedding = question_embedding
    hits = util.semantic_search(question_embedding, topic_embedding_tensor, top_k=candidate_num)
    hits = hits[0]

    # clustering
    start_time = time.time()
    cluster_topic_embedding = np.stack([topic_embedding_tensor[hit['corpus_id']] for hit in hits])
    print(len(cluster_topic_embedding))
    print(cluster_topic_embedding[0].shape)
    clusters = util.community_detection(cluster_topic_embedding, min_community_size=1, threshold=0.99)
    print("Clustering done after {:.2f} sec".format(time.time() - start_time))
    clusters = [[hits[cid]['corpus_id'] for cid in l] for l in clusters]
    print("number of clusters", len(clusters))

    # cross-encoder
    cross_inp = [[question, text_list[hit['corpus_id']]] for hit in hits]
    cross_scores = ce_model.predict(cross_inp)
    for idx in range(len(cross_scores)):
            hits[idx]['cross-score'] = cross_scores[idx]

    bi_hits = sorted(hits, key=lambda x: x['score'], reverse=True)
    ce_hits = sorted(hits, key=lambda x: x['cross-score'], reverse=True)
    
    bi_list = bi_hits[0:returned_top_k]    
    cad_ce_list = ce_hits[0:candidate_num]
    
    ce_list = []
    ce_dict_list = [] 
    selected_cluster_id =[]
    for c in cad_ce_list:
        c_id = get_cluster_list(c['corpus_id'], clusters)
        if (
            (c_id is not None) and 
            (c_id not in selected_cluster_id) and 
            (len(ce_list)<returned_top_k)
        ):
            selected_cluster_id.append(c_id)
            doc = Document(
                page_content=text_list[c['corpus_id']], 
                metadata={
                    "corpus_id": c['corpus_id'],
                    "score": c['score'],
                    "cross-score": c['cross-score'],
                    "title":query_list[c['corpus_id']].strip(),
                    "url": url_list[c['corpus_id']],
                    })
            doc_dict = {}
            doc_dict['metadata'] = {}
            doc_dict['page_content'] = str(text_list[c['corpus_id']])
            doc_dict['metadata']['corpus_id'] = str(c['corpus_id'])
            doc_dict['metadata']['score'] = str(c['score'])
            doc_dict['metadata']['cross-score'] = str(c['cross-score'])
            doc_dict['metadata']['title'] = str(query_list[c['corpus_id']].strip())
            doc_dict['metadata']['url'] = str(url_list[c['corpus_id']])

            ce_list.append(doc)
            ce_dict_list.append(doc_dict)

        if c_id == None:
            print("!!!!!!!!!!!!!!!")    
    
    print(json.loads(json.dumps(ce_dict_list)))

    return jsonify({
        "message": json.loads(json.dumps(ce_dict_list))
    }), 200


@app.route('/health', methods=['GET'])
def health():
    resp = jsonify({"message": json.dumps('[BI/CE] Hello! Up and running. ', default=vars)})
    resp.status_code = 200
    return resp 





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8089)
