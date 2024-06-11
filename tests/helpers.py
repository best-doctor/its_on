import datetime

from freezegun import freeze_time
from pydantic import PostgresDsn
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine

from auth.models import users
from its_on.db_utils import db_name_from_dsn
from its_on.models import switches, user_switches, switch_history
from its_on.settings import Settings


def get_engine(dsn: PostgresDsn) -> Engine:
    return create_engine(str(dsn), isolation_level='AUTOCOMMIT')


def setup_db(settings: Settings) -> None:
    """Настройка тестовой БД.

    Удаляем старую тестовую базу и создаем новую.
    """
    engine = get_engine(settings.database_superuser_dsn)

    with engine.connect() as conn:
        teardown_db(settings)

        test_db_name = db_name_from_dsn(settings.database_dsn)
        conn.execute('CREATE DATABASE {0}'.format(test_db_name))


def teardown_db(settings: Settings) -> None:
    """Удаление тестовой БД."""
    engine = get_engine(settings.database_superuser_dsn)

    test_db_name = db_name_from_dsn(settings.database_dsn)
    with engine.connect() as conn:
        # Отключаем активные сессии
        conn.execute(
            """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{0}' AND pid <> pg_backend_pid();
            """.format(
                test_db_name,
            ),
        )
        # Удаляем базу
        conn.execute('DROP DATABASE IF EXISTS {0}'.format(test_db_name))


def create_tables(settings: Settings) -> None:
    engine = get_engine(settings.database_dsn)

    meta = MetaData()
    meta.create_all(bind=engine, tables=[switches, users, user_switches, switch_history])


def drop_tables(settings: Settings) -> None:
    engine = get_engine(settings.database_dsn)

    meta = MetaData()
    meta.drop_all(bind=engine, tables=[switches, users, user_switches, switch_history])


@freeze_time(datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc))
def create_sample_data(settings: Settings) -> None:
    engine = get_engine(settings.database_dsn)

    with engine.connect() as conn:
        conn.execute(
            switches.insert(),
            [
                {
                    'name': 'switch1',
                    'is_active': True,
                    'deleted_at': None,
                    'groups': ('group1', 'group2'),
                    'version': None,
                },
                {
                    'name': 'switch2',
                    'is_active': True,
                    'deleted_at': None,
                    'groups': ('group1',),
                    'version': None,
                },
                {
                    'name': 'switch3',
                    'is_active': False,
                    'deleted_at': None,
                    'groups': ('group1',),
                    'version': 4,
                },
                {
                    'name': 'switch4',
                    'is_active': True,
                    'deleted_at': None,
                    'groups': ('group1', 'group3'),
                    'version': 4,
                },
                {
                    'name': 'switch5',
                    'is_active': True,
                    'deleted_at': None,
                    'groups': ('group2',),
                    'version': 4,
                },
                {
                    'name': 'switch6',
                    'is_active': True,
                    'deleted_at': datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc),
                    'groups': ('group2',),
                    'version': 4,
                },
                {
                    'name': 'switch7',
                    'is_active': True,
                    'deleted_at': None,
                    'groups': ('soft_delete',),
                    'version': None,
                },
                {
                    'id': 8,
                    'name': 'switch8',
                    'is_active': True,
                    'deleted_at': datetime.datetime(2020, 5, 15, tzinfo=datetime.timezone.utc),
                    'groups': ('group2',),
                    'version': 4,
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
