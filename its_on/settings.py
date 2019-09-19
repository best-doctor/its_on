import os
from typing import Dict

DEBUG = bool(os.environ.get('DEBUG', False))
SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')
SERVER_PORT = os.environ.get('SERVER_PORT', 8081)
DATABASE_DSN = os.environ.get('DATABASE_DSN', 'postgresql://bestdoctor:bestdoctor@localhost:5432/its_on')
CACHE_URL = os.environ.get('CACHE_URL', 'memory://')


def get_config() -> Dict:
    return {
        'debug': DEBUG,
        'host': SERVER_HOST,
        'port': SERVER_PORT,
        'database_dsn': DATABASE_DSN,
        'cache_url': CACHE_URL,
    }
