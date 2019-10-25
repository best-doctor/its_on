from dynaconf.base import Settings
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine.strategies import EngineStrategy

from auth.models import users
from its_on.db_utils import parse_dsn
from its_on.models import switches, user_switches


def get_engine(dsn: str) -> EngineStrategy:
    return create_engine(dsn, isolation_level='AUTOCOMMIT')


def setup_db(config: Settings) -> None:
    """Настройка тестовой БД.

    Удаляем старую тестовую базу и создаем новую.
    """
    engine = get_engine(config.DATABASE.SUPERUSER_DSN)

    with engine.connect() as conn:
        teardown_db(config)

        test_db_name = parse_dsn(config.DATABASE.DSN)['database']
        conn.execute('CREATE DATABASE {0}'.format(test_db_name))


def teardown_db(config: Settings) -> None:
    """Удаление тестовой БД."""
    engine = get_engine(config.DATABASE.SUPERUSER_DSN)

    test_db_name = parse_dsn(config.DATABASE.DSN)['database']
    with engine.connect() as conn:
        # Отключаем активные сессии
        conn.execute(
            """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{0}' AND pid <> pg_backend_pid();
            """.format(test_db_name),
        )
        # Удаляем базу
        conn.execute('DROP DATABASE IF EXISTS {0}'.format(test_db_name))


def create_tables(config: Settings) -> None:
    engine = get_engine(config.DATABASE.DSN)

    meta = MetaData()
    meta.create_all(bind=engine, tables=[switches, users, user_switches])


def drop_tables(config: Settings) -> None:
    engine = get_engine(config.DATABASE.DSN)

    meta = MetaData()
    meta.drop_all(bind=engine, tables=[switches, users, user_switches])


def create_sample_data(config: Settings) -> None:
    engine = get_engine(config.DATABASE.DSN)

    with engine.connect() as conn:
        conn.execute(
            switches.insert(),
            [
                {'name': 'switch1', 'is_active': True, 'is_hidden': False, 'group': 'group1', 'version': None},
                {'name': 'switch2', 'is_active': True, 'is_hidden': False, 'group': 'group1', 'version': None},
                {'name': 'switch3', 'is_active': False, 'is_hidden': False, 'group': 'group1', 'version': 4},
                {'id': 4, 'name': 'switch4', 'is_active': True, 'is_hidden': False, 'group': 'group1', 'version': 4},
                {'id': 5, 'name': 'switch5', 'is_active': True, 'is_hidden': False, 'group': 'group2', 'version': 4},
                {'id': 6, 'name': 'switch6', 'is_active': True, 'is_hidden': True, 'group': 'group2', 'version': 4},
                {
                    'id': 7,
                    'name': 'switch7',
                    'is_active': True,
                    'is_hidden': False,
                    'group': 'soft_delete',
                    'version': None,
                },
            ],
        )
        conn.execute(
            users.insert(),
            [
                {
                    'id': 1,
                    'login': 'admin',
                    'passwd': '$5$rounds=535000$WLLTOp3BDURUJCpA$W0CZSO1mR8/OfIPKj/piXv9cBIXBhlnDpQcORnnQR5/',
                    'is_superuser': True,
                    'disabled': False,
                },
                {
                    'id': 2,
                    'login': 'user1',
                    'passwd': '$5$rounds=535000$WLLTOp3BDURUJCpA$W0CZSO1mR8/OfIPKj/piXv9cBIXBhlnDpQcORnnQR5/',
                    'is_superuser': False,
                    'disabled': False,
                },
            ],
        )
        conn.execute(
            user_switches.insert(),
            [
                {'user_id': 1, 'switch_id': 4},
                {'user_id': 1, 'switch_id': 5},
                {'user_id': 1, 'switch_id': 6},
                {'user_id': 2, 'switch_id': 7},
            ],
        )
