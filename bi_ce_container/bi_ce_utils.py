import os 
import json
import yaml

import torch
from torch import Tensor


def load_config(config_file=None):
    """
    Load the configuration file. Override if an environment 
    variable is set.

    :param config_file:
    :return config:
    """    
    if not config_file:
        # Default configuration file
        config_file = 'config/bi_ce_module_config.yaml'
        
    # Override if an environment variable is set
    if 'CONFIG_FILE' in os.environ:
        config_file = os.environ['CONFIG_FILE']
    
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        config = config['bice_encoder']
        return config


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


def ciscocom_merged_data_reader(file_path):
    """
    Read the cisco.com merged data
    
    :param file_path:
    :return title_list:
    :return text_list:
    """
    with open(file_path, 'r') as file:
        json_data= json.load(file)
    title_list = []
    text_list = []
    for d in json_data:
        title_list.append(json.loads(d)['key'])
        text_list.append(json.loads(d)['value'])
    return title_list, text_list

