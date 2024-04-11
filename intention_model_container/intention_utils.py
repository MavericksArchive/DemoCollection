import os
import yaml


def load_config(config_file=None):
    """
    Load the configuration file. Override if an environment 
    variable is set.

    :param config_file:
    :return config:
    """    
    if not config_file:
        # Default configuration file
        config_file = 'config/intention_module_config.yaml'
        
    # Override if an environment variable is set
    if 'CONFIG_FILE' in os.environ:
        config_file = os.environ['CONFIG_FILE']
    
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        return config
    