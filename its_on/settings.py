import os
import pathlib
from copy import copy
from typing import Dict

from its_on.db import parse_dsn, make_dsn

BASE_DIR = pathlib.Path(__file__).parent.parent

TESTING = bool(os.environ.get('TESTING', False))

DEBUG = bool(os.environ.get('DEBUG', False))
SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')
SERVER_PORT = os.environ.get('SERVER_PORT', 8081)
DATABASE_DSN = os.environ.get('DATABASE_DSN', 'postgresql://bestdoctor:bestdoctor@localhost:5432/its_on')

CACHE_URL = os.environ.get('CACHE_URL', 'memory://')
ENABLE_DEBUG_DB_LOGGING = bool(os.environ.get('ENABLE_DEBUG_DB_LOGGING', False))


def get_config() -> Dict:
    config = {
        'testing': TESTING,
        'debug': DEBUG,
        'host': SERVER_HOST,
        'port': SERVER_PORT,
        'database_dsn': DATABASE_DSN,
        'cache_url': CACHE_URL,
        'enable_debug_db_logging': ENABLE_DEBUG_DB_LOGGING,
    }
    database = parse_dsn(DATABASE_DSN)
    test_database_dsn: str
    test_database: Dict

    if TESTING:
        test_database = copy(database)
        test_database['database'] = 'test_{0}'.format(test_database['database'])
        test_database_dsn = make_dsn(**test_database)

    config['test_database'] = test_database
    config['test_database_dsn'] = test_database_dsn
    config['database'] = database

    return config
