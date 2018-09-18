import logging
from logging.handlers import RotatingFileHandler
import os

def init_logging(config, output_dir):
    if config['level'] == 'INFO':
        level = logging.INFO
    elif config['level'] == 'DEBUG':
        level = logging.DEBUG
    elif config['level'] == 'WARNING':
        level = logging.WARNING
    else:
        level = logging.ERROR
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(level)
    formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(processName)s] [%(levelname)-5.5s]  %(message)s", datefmt='%H:%M:%S')
    c_handler.setFormatter(formatter)
    logger.addHandler(c_handler)

    # create error file handler and set level to error
    handler = RotatingFileHandler(os.path.join(output_dir, "error.log"),"a", maxBytes=10240, backupCount=5)
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(processName)s] [%(levelname)-5.5s]  %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if config['debug_file_logging'] == True:
        # create debug file handler and set level to debug
        handler = RotatingFileHandler(os.path.join(output_dir, "debug.log"),"a", maxBytes=10240, backupCount=5)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(processName)s] [%(levelname)-5.5s]  %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
