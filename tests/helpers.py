from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine.strategies import EngineStrategy
from typing import Dict

from its_on.db_utils import parse_dsn
from its_on.models import switches


def setup_db(config: Dict) -> None:
    engine = get_engine(config.DATABASE.SUPERUSER_DSN)

    with engine.connect() as conn:
        teardown_db(config)

        test_db_name = parse_dsn(config.DATABASE.DSN)['database']

        conn.execute('CREATE DATABASE {0}'.format(test_db_name))


def teardown_db(config: Dict) -> None:
    engine = get_engine(config.DATABASE.SUPERUSER_DSN)

    test_db_name = parse_dsn(config.DATABASE.DSN)['database']

    with engine.connect() as conn:
        conn.execute("""
                  SELECT pg_terminate_backend(pg_stat_activity.pid)
                  FROM pg_stat_activity
                  WHERE pg_stat_activity.datname = '{0}'
                    AND pid <> pg_backend_pid();""".format(test_db_name))
        conn.execute('DROP DATABASE IF EXISTS {0}'.format(test_db_name))


def get_engine(dsn: str) -> EngineStrategy:
    return create_engine(dsn, isolation_level='AUTOCOMMIT')


def create_tables(config: Dict) -> None:
    engine = get_engine(config.DATABASE.DSN)

    meta = MetaData()
    meta.create_all(bind=engine, tables=[switches])


def drop_tables(config: Dict) -> None:
    engine = get_engine(config.DATABASE.DSN)

    meta = MetaData()
    meta.drop_all(bind=engine, tables=[switches])


def create_sample_data(config: Dict) -> None:
    engine = get_engine(config.DATABASE.DSN)

    with engine.connect() as conn:
        conn.execute(
            switches.insert(),
            [
                {'name': 'switch1', 'is_active': True, 'group': 'group1', 'version': None},
                {'name': 'switch2', 'is_active': True, 'group': 'group1', 'version': None},
                {'name': 'switch3', 'is_active': False, 'group': 'group1', 'version': 4},
                {'name': 'switch4', 'is_active': True, 'group': 'group1', 'version': 4},
                {'name': 'switch5', 'is_active': True, 'group': 'group2', 'version': 4},
            ],
        )
