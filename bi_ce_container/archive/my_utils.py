import requests
from torch import Tensor, device
from typing import List, Callable
from tqdm.autonotebook import tqdm
import sys
import importlib
import os
import torch
import numpy as np
import queue
import logging
from typing import Dict, Optional, Union
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_url, cached_download, HfFolder
from huggingface_hub.constants import HUGGINGFACE_HUB_CACHE
import fnmatch
from packaging import version
import transformers
import json
import pandas as pd 
from sentence_transformers import util


space_len = 10 

def http_get(url, path):
    """
    Downloads a URL to a given path on disc
    """
    if os.path.dirname(path) != '':
        os.makedirs(os.path.dirname(path), exist_ok=True)

    req = requests.get(url, stream=True)
    if req.status_code != 200:
        print("Exception when trying to download {}. Response {}".format(url, req.status_code), file=sys.stderr)
        req.raise_for_status()
        return

    download_filepath = path+"_part"
    with open(download_filepath, "wb") as file_binary:
        content_length = req.headers.get('Content-Length')
        total = int(content_length) if content_length is not None else None
        progress = tqdm(unit="B", total=total, unit_scale=True)
        for chunk in req.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                progress.update(len(chunk))
                file_binary.write(chunk)

    os.rename(download_filepath, path)
    progress.close()

def snapshot_download(
    repo_id: str,
    revision: Optional[str] = None,
    cache_dir: Union[str, Path, None] = None,
    library_name: Optional[str] = None,
    library_version: Optional[str] = None,
    user_agent: Union[Dict, str, None] = None,
    ignore_files: Optional[List[str]] = None,
    use_auth_token: Union[bool, str, None] = None
) -> str:
    """
    Method derived from huggingface_hub.
    Adds a new parameters 'ignore_files', which allows to ignore certain files / file-patterns
    """
    if cache_dir is None:
        cache_dir = HUGGINGFACE_HUB_CACHE
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)

    _api = HfApi()
    
    token = None 
    if isinstance(use_auth_token, str):
        token = use_auth_token
    elif use_auth_token:
        token = HfFolder.get_token()
        
    model_info = _api.model_info(repo_id=repo_id, revision=revision, token=token)

    storage_folder = os.path.join(
        cache_dir, repo_id.replace("/", "_")
    )

    all_files = model_info.siblings
    #Download modules.json as the last file
    for idx, repofile in enumerate(all_files):
        if repofile.rfilename == "modules.json":
            del all_files[idx]
            all_files.append(repofile)
            break

    for model_file in all_files:
        if ignore_files is not None:
            skip_download = False
            for pattern in ignore_files:
                if fnmatch.fnmatch(model_file.rfilename, pattern):
                    skip_download = True
                    break

            if skip_download:
                continue

        url = hf_hub_url(
            repo_id, filename=model_file.rfilename, revision=model_info.sha
        )
        relative_filepath = os.path.join(*model_file.rfilename.split("/"))

        # Create potential nested dir
        nested_dirname = os.path.dirname(
            os.path.join(storage_folder, relative_filepath)
        )
        os.makedirs(nested_dirname, exist_ok=True)

        cached_download_args = {'url': url,
            'cache_dir': storage_folder,
            'force_filename': relative_filepath,
            'library_name': library_name,
            'library_version': library_version,
            'user_agent': user_agent,
            'use_auth_token': use_auth_token}

        if version.parse(huggingface_hub.__version__) >= version.parse("0.8.1"):
            # huggingface_hub v0.8.1 introduces a new cache layout. We sill use a manual layout
            # And need to pass legacy_cache_layout=True to avoid that a warning will be printed
            cached_download_args['legacy_cache_layout'] = True

        path = cached_download(**cached_download_args)

        if os.path.exists(path + ".lock"):
            os.remove(path + ".lock")

    return storage_folder

def fullname(o):
  """
  Gives a full name (package_name.class_name) for a class / object in Python. Will
  be used to load the correct classes from JSON files
  """

  module = o.__class__.__module__
  if module is None or module == str.__class__.__module__:
    return o.__class__.__name__  # Avoid reporting __builtin__
  else:
    return module + '.' + o.__class__.__name__
  
def batch_to_device(batch, target_device: device):
    """
    send a pytorch batch to a device (CPU/GPU)
    """
    for key in batch:
        if isinstance(batch[key], Tensor):
            batch[key] = batch[key].to(target_device)
    return batch

def import_from_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        raise ImportError(msg)

    try:
        module = importlib.import_module(dotted_path)
    except:
        module = importlib.import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (module_path, class_name)
        raise ImportError(msg)
    
def smart_batching_collate(batch, tokenizer, device="cuda"):
        num_texts = len(batch[0].texts)
        texts = [[] for _ in range(num_texts)]
        labels = []

        for example in batch:
            for idx, text in enumerate(example.texts):
                texts[idx].append(text)

            labels.append(example.label)

        labels = torch.tensor(labels)

        sentence_features = []
        for idx in range(num_texts):
            tokenized = tokenizer(texts[idx], return_tensors="pt",padding=True).to("cuda")
            sentence_features.append(tokenized)

        return sentence_features, labels

def pairwise_dot_score(a: Tensor, b: Tensor):
    """
   Computes the pairwise dot-product dot_prod(a[i], b[i])

   :return: Vector with res[i] = dot_prod(a[i], b[i])
   """
    if not isinstance(a, torch.Tensor):
        a = torch.tensor(a)

    if not isinstance(b, torch.Tensor):
        b = torch.tensor(b)

    return (a * b).sum(dim=-1)


def save_model(model, saved_path):
    model_config= {
        'sentence_transformers': '1.0',
        'transformers': transformers.__version__,
        'pytorch': torch.__version__,
    }

    with open(os.path.join(saved_path, 'config_sentence_transformers.json'), 'w') as fOut:
        json.dump(model_config, fOut, indent=2)
    model.auto_model.save_pretrained(saved_path+"/")
    model.tokenizer.save_pretrained(saved_path+"/")

def save_model_ce_model(model, saved_path):
    model_config= {
        'sentence_transformers': '1.0',
        'transformers': transformers.__version__,
        'pytorch': torch.__version__,
    }

    with open(os.path.join(saved_path, 'config_sentence_transformers.json'), 'w') as fOut:
        json.dump(model_config, fOut, indent=2)
    model.model.save_pretrained(saved_path+"/")
    model.tokenizer.save_pretrained(saved_path+"/")


def cisco_com_dataset_reader(directory_path = '/home/ubuntu/qigong/codeLLM/datasets/CISCOCOM/data/', recursively=True, withTitle=False, sec_len=-1, sub_sec_len=-1):    
    json_files = get_json_file_list(directory_path)

    dataset = []
    for f in tqdm(json_files):
        file_name = directory_path+f
        data = extract_topic_from_json(file_name, recursively=recursively, withTitle=withTitle, sec_len=sec_len, sub_sec_len=sub_sec_len)
        dataset.extend(data)


    deduplicated_mapping = remove_duplicated(dataset)
    text_list = []
    title_list = []

    for idx, r in tqdm(enumerate(deduplicated_mapping)):
        # text_list.append(r['key']+"\n"+r['value'])
        text_list.append(r['value'])
        title_list.append(r['key'])

    return title_list, text_list

def gnosis_dataset_read(directory_path = '/home/ubuntu/qigong/codeLLM/datasets/gnosis/data_gnosis.json'):
    with open(directory_path) as file:
        json_data = json.load(file)

    dataset = []
    for _, r in tqdm(enumerate(json_data), total=len(json_data)):
        str_title = r['title'].strip()
        str_desc = r['desc'].strip()
        if len(str_title.split(" "))>1 and str_desc!="":
            dataset.append({'key':str_title, 'value':str_desc})

    deduplicated_mapping = remove_duplicated(dataset)

    text_list = []
    title_list = []

    for idx, r in tqdm(enumerate(deduplicated_mapping), total=len(deduplicated_mapping)):
        title_list.append(r['key'])
        text_list.append(r['value'])
    return title_list, text_list

def sr_dataset_reader(file_path = '/home/ubuntu/qigong/codeLLM/datasets/sr/SR_data.xlsx', key_col_name = "PROBLEM_DESCRIPTION", val_col_name="KT_PROBLEM_ANALYSIS"):
    
    dataset = []
    df = pd.read_excel(file_path, sheet_name='Sheet1')

    #remove empty value rows 
    df = df.dropna(subset=[key_col_name])
    df = df.dropna(subset=[val_col_name])

    for _,r in tqdm(df.iterrows(), total=df.shape[0]):
        # at least two words in the text 
        str_key = str(r[key_col_name]).strip()
        str_value = str(r[val_col_name]).strip()
        if len(str_key.split(" "))>1 and len(str_value.split(" "))>1:
            dataset.append({'key':str_key, 'value':str_value})
    deduplicated_mapping = remove_duplicated(dataset)
    
    text_list = []
    title_list = []

    for idx, r in tqdm(enumerate(deduplicated_mapping), total=len(deduplicated_mapping)):
        title_list.append(r['key'])
        text_list.append(r['value'])
    return title_list, text_list, [key_col_name, val_col_name]

def ciscocom_merged_data_reader(file_path):
    with open(file_path, 'r') as file:
        json_data= json.load(file)
    title_list = []
    text_list = []
    for d in json_data:
        title_list.append(json.loads(d)['key'])
        text_list.append(json.loads(d)['value'])
    return title_list, text_list

def get_json_file_list(directory_path):
    # List all files in the directory
    files_in_directory = os.listdir(directory_path)
    # Filter out files with a .json extension
    json_files = [file for file in files_in_directory if file.endswith('.json')]
    return json_files

def print_json_rec(pre_topic, item, data:list, space="", recursively=False, verbose=True, withTitle=False,sec_len=-1, sub_sec_len=3):
    returned_str = ""
    
    for sub in item:
        if verbose:
            print(space+pre_topic+","+sub['title'])
        new_pre_topic = pre_topic+", "+sub['title']
        
        if recursively: 
            if sub["text"]!='' and len(sub["text"])!=0:
                if sub_sec_len>0:
                    returned_str+= sub['title']+" : "+"\n".join(sub["text"][:sub_sec_len])+"\n"
                else:
                    returned_str+= sub['title']+" : "+"\n".join(sub["text"])+"\n"
            
            if 'sub_items' in sub:
                space = space+" "*space_len
                returned_str += sub['title']+" : " +print_json_rec(new_pre_topic, sub['sub_items'], None, space, recursively, verbose=verbose)

        if 'sub_items' in sub:
            if recursively:
                sub_summary_str = print_json_rec(new_pre_topic, sub['sub_items'], data, space, recursively, verbose=False)
            else:
                sub_summary_str = ""
            
            if sub["text"]!='' and len(sub["text"])!=0:
                if sec_len > 0:
                    sub_str = "\n".join(sub["text"][:sec_len])+"\n"+sub_summary_str
                else:
                    sub_str = "\n".join(sub["text"])+"\n"+sub_summary_str
            else:
                sub_str = sub_summary_str
        else:
            if sub["text"]!='' and len(sub["text"])!=0:
                sub_str = "\n".join(sub["text"])
            else:
                sub_str = ""
            
        if withTitle:
            sub_str = new_pre_topic+" : \n"+ sub_str

        if data!=None and (sub_str!='' and sub_str!=0):
            data.append({"key":new_pre_topic, "value":sub_str})

    if recursively:
        return returned_str
    else:
        return ""

def extract_topic_from_json(file_path:str, recursively=False, withTitle=False, sec_len=-1, sub_sec_len=3):
    extracted_data = []
    with open(file_path, 'r') as file:
        data = json.load(file)

        for d in data:
            top_title = d['top_title']

            top_url = d['top_url']

            for h1 in d['H1_topics']:
                H1_title = h1['H1_title']
                H1_url = h1['H1_url']

                if 'sub_topics' in h1:
                    print_json_rec(top_title+", "+h1['H1_title'], h1['sub_topics'], extracted_data, "" , recursively=recursively, verbose=False, withTitle=withTitle, sec_len=sec_len, sub_sec_len=sub_sec_len)
    return extracted_data

def remove_duplicated(data:list)->list:
    print("Before deduplicating:", len(data))
    aggregated = {}
    for m in tqdm(data):
        if m['key'] not in aggregated:
            aggregated[m['key']] = m['value']
        # else:
            # aggregated[m['key']] += "\n" + m['value']

    # Convert the aggregated dictionary back to a list of dictionaries
    deduplicated_mapping = [{'key': k, 'value': v} for k, v in aggregated.items()]
    print("After deduplicating", len(deduplicated_mapping))
    return deduplicated_mapping


def sbert_query(question, bi_model, ce_model, topic_embedding_tensor, text_list, candidata_num = 512, returned_topk=5):

    if topic_embedding_tensor.shape[0] != len(text_list):
        print("Please guarantee the embedding and source doccuments have the same size. ")
        return None
        

    question_embedding = bi_model.encode([question], show_bar=False)
    question_embedding = question_embedding
    hits = util.semantic_search(question_embedding, topic_embedding_tensor, top_k=candidata_num)
    hits = hits[0]

    cluster_topic_embedding = np.stack([topic_embedding_tensor[hit['corpus_id']] for hit in hits])
    clusters = util.community_detection(cluster_topic_embedding, min_community_size=1, threshold=0.99)
    clusters = [[hits[cid]['corpus_id'] for cid in l] for l in clusters]

    cross_inp = [[question, text_list[hit['corpus_id']]] for hit in hits]
    cross_scores = ce_model.predict(cross_inp)
    for idx in range(len(cross_scores)):
            hits[idx]['cross-score'] = cross_scores[idx]

    bi_hits = sorted(hits, key=lambda x: x['score'], reverse=True)
    ce_hits = sorted(hits, key=lambda x: x['cross-score'], reverse=True)
    
    bi_list = bi_hits[0:returned_topk]
    
    cad_ce_list = ce_hits[0:candidata_num]
    
    ce_list = []
    selected_cluster_id =[]
    for c in cad_ce_list:
        c_id = get_cluster_list(c['corpus_id'], clusters)
        if c_id!=None and c_id not in selected_cluster_id and len(ce_list)<returned_topk:
             selected_cluster_id.append(c_id)
             ce_list.append(c)
        if c_id == None:
             print(f"Clsuter id {c_id} can not find in Cluster !!!!!!!!!!!!!!!")    
    
    return bi_list, ce_list

def get_cluster_list(corpus_id, cluster_list):
    for l_id, l in enumerate(cluster_list):
         if corpus_id in l:
            return l_id
    return None
