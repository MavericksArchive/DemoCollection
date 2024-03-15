import yaml
import logging
from pathlib import Path
from datetime import datetime


def setup_logging(log_name):
    """set up logging"""
    base_dir = Path('..')
    if not (base_dir/'logs').is_dir():
        base_dir = Path('.')
        (base_dir/'logs').is_dir()
    start_time = f'{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}'
    assert isinstance(log_name, str)
    assert isinstance(start_time, str)
    log_filename = f'{log_name}_{start_time}.log'
    log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(base_dir / 'logs' / log_filename),
            logging.StreamHandler()
        ])
    
    # suppressing 3rd party logger ('absl') INFO level ... 
    supp_logger = logging.getLogger('absl')
    supp_logger.setLevel(logging.WARNING)
    
    # suppressing 3rd party logger ('langchain.utils.math') INFO level ... 
    supp_logger = logging.getLogger('langchain.utils.math')
    supp_logger.setLevel(logging.WARNING)

    logging.info(f'log_filename: {log_filename}')
    logging.info(f'start_time: {start_time}')
    logging.info(f'Start setting up ...')
    return log_filename


def read_yaml(config_file_name):
    with open(config_file_name, 'r') as config_file:
        try:
            config = yaml.safe_load(config_file)
        except yaml.YAMLError as exc:
            print(exc)
    return config
