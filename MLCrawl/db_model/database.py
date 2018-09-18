from sqlalchemy import create_engine
import os

def initialize_db(config, root_dir):
    if config['dialect'] == 'sqlite':
        adress = 'sqlite:///{}'.format(os.path.join(root_dir, config['name']))
    else:
        adress = '{}+{}://{}:{}@{}:{}/{}'.format(config['dialect'],
                                                 config['driver'],
                                                 config['username'],
                                                 config['password'],
                                                 config['host'],
                                                 config['port'],
                                                 config['name'])

    engine = create_engine(adress)
    return engine
