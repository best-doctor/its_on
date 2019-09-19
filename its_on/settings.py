import os
from typing import Dict

DEBUG = bool(os.environ.get('DEBUG', False))
SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')
SERVER_PORT = os.environ.get('SERVER_PORT', 8081)
DATABASE_DSN = os.environ.get('DATABASE_DSN', 'postgresql://bestdoctor:bestdoctor@localhost:5432/its_on')
CACHE_URL = os.environ.get('CACHE_URL', 'memory://')
ENABLE_DEBUG_DB_LOGGING = bool(os.environ.get('ENABLE_DEBUG_DB_LOGGING', False))


def get_config() -> Dict:
    return {
        'debug': DEBUG,
        'host': SERVER_HOST,
        'port': SERVER_PORT,
        'database_dsn': DATABASE_DSN,
        'cache_url': CACHE_URL,
        'enable_debug_db_logging': ENABLE_DEBUG_DB_LOGGING,
    }
