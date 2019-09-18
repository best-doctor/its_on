from typing import Dict

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
        'host': 'localhost',
        'port': SERVER_PORT,
        'postgres': DATABASE,
    }
