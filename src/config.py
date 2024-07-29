import os
import importlib

env = os.environ.get('APP_ENV', 'development')
config = importlib.import_module(f'config_{env}')

