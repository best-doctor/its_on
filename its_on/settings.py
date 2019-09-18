import os
from typing import Dict

DEBUG = bool(os.environ.get("DEBUG", False))
SERVER_HOST = 'localhost'
SERVER_PORT = 8081
DATABASE = {
    'host': 'localhost',
    'port': 5432,
    'name': 'its_on',
    'user': 'bestdoctor',
    'password': 'bestdoctor',
}


def get_config() -> Dict:
    return {
        'debug': DEBUG,
        'host': SERVER_HOST,
        'port': SERVER_PORT,
        'postgres': DATABASE,
    }
