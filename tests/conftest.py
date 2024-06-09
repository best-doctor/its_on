import datetime
from typing import Callable, Generator
from unittest.mock import MagicMock

import pytest
import factory.fuzzy
from anybadge import Badge
from anybadge.config import MASK_ID_PREFIX
from sqlalchemy.orm import Session

from its_on.main import init_gunicorn_app
from its_on.models import switches
from its_on.settings import settings
from its_on.utils import utc_now, localize_datetime
from .helpers import (
    create_sample_data, create_tables, drop_tables, setup_db, teardown_db, get_engine,
)


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


@pytest.fixture()
async def client(aiohttp_client: Callable) -> None:
    app = await init_gunicorn_app()
    return await aiohttp_client(app)


@pytest.fixture()
def db_conn_acquirer(client) -> Callable:
    return client.server.app['db'].acquire


@pytest.fixture()
async def switch(db_conn_acquirer):
    async with db_conn_acquirer() as conn:
        result = await conn.execute(switches.select().where(switches.c.id == 1))
        return await result.first()


@pytest.fixture()
async def login(client):
    await client.post('/zbs/login', data={'login': 'admin', 'password': 'password'})


@pytest.fixture()
async def user_login(client):
    await client.post('/zbs/login', data={'login': 'user1', 'password': 'password'})


@pytest.fixture(scope='session')
def setup_database() -> Generator:
    setup_db(settings=settings)
    yield
    teardown_db(settings=settings)


@pytest.fixture(scope='function')
def setup_tables(setup_database: Callable) -> Generator:
    create_tables(settings=settings)
    yield
    drop_tables(settings=settings)


@pytest.fixture(scope='function')
def setup_tables_and_data(setup_tables: Callable) -> Generator:
    create_sample_data(settings=settings)
    yield


@pytest.fixture(scope='function')
def switches_full_info_expected_result():
    return {
        'result': [
            {
                'name': 'switch1',
                'is_active': True,
                'is_hidden': False,
                'groups': ['group1', 'group2'],
                'version': None,
                'comment': None,
                'created_at': '2020-04-15T00:00:00+00:00',
            },
            {
                'name': 'switch2',
                'is_active': True,
                'is_hidden': False,
                'groups': ['group1'],
                'version': None,
                'comment': None,
                'created_at': '2020-04-15T00:00:00+00:00',
            },
            {
                'name': 'switch3',
                'is_active': False,
                'is_hidden': False,
                'groups': ['group1'],
                'version': 4,
                'comment': None,
                'created_at': '2020-04-15T00:00:00+00:00',
            },
            {
                'name': 'switch4',
                'is_active': True,
                'is_hidden': False,
                'groups': ['group1', 'group3'],
                'version': 4,
                'comment': None,
                'created_at': '2020-04-15T00:00:00+00:00',
            },
            {
                'name': 'switch5',
                'is_active': True,
                'is_hidden': False,
                'groups': ['group2'],
                'version': 4,
                'comment': None,
                'created_at': '2020-04-15T00:00:00+00:00',
            },
            {
                'name': 'switch6',
                'is_active': True,
                'is_hidden': True,
                'groups': ['group2'],
                'version': 4,
                'comment': None,
                'created_at': '2020-04-15T00:00:00+00:00',
            },
            {
                'name': 'switch7',
                'is_active': True,
                'is_hidden': False,
                'groups': ['soft_delete'],
                'version': None,
                'comment': None,
                'created_at': '2020-04-15T00:00:00+00:00',
            },
        ],
    }


@pytest.fixture(scope='function')
def asserted_switch_full_info_data(client):
    def _with_params(switches_list: list) -> dict:
        return {
            'result': [
                {
                    'name': switch.name,
                    'is_active': switch.is_active,
                    'is_hidden': switch.is_hidden,
                    'groups': switch.groups,
                    'version': switch.version,
                    'comment': switch.comment,
                    'ttl': switch.ttl,
                    'created_at': switch.created_at.astimezone(datetime.timezone.utc).isoformat(),
                    'updated_at': switch.updated_at.astimezone(datetime.timezone.utc).isoformat(),
                    'deleted_at': (
                        switch.deleted_at.astimezone(datetime.timezone.utc).isoformat()
                        if switch.deleted_at else None
                    ),
                    'flag_url': str(client.make_url(f'/zbs/switches/{switch.id}')),
                } for switch in switches_list
            ],
        }

    return _with_params


@pytest.fixture(scope='function')
def get_switches_data_mocked_existing_switch(mocker):
    mock = mocker.patch(
        'its_on.admin.views.switches.SwitchesCopyAdminView._get_switches_data',
        new_callable=AsyncMock,
    )
    mock.return_value = {
        'result': [
            {
                'name': 'switch7',
                'is_active': False,
                'is_hidden': False,
                'groups': ['soft_delete'],
                'version': 2,
                'comment': '',
                'created_at': '2020-10-30T10:00:12.000000+00:00',
                'updated_at': '2020-10-30T10:00:12.000000+00:00',
                'flag_url': 'http://test.ru/zbs/switches/10557',
            },
        ],
    }
    return mock


@pytest.fixture(scope='function')
def get_switches_data_mocked_new_switch(mocker):
    mock = mocker.patch(
        'its_on.admin.views.switches.SwitchesCopyAdminView._get_switches_data',
        new_callable=AsyncMock,
    )
    mock.return_value = {
        'result': [
            {
                'name': 'extremely_new_switch',
                'is_active': True,
                'is_hidden': False,
                'groups': [],
                'version': 8,
                'comment': '',
            },
        ],
    }
    return mock


@pytest.fixture()
def switch_to_json_factory():
    def switch_to_json(switch):
        return {
            'name': switch.name,
            'is_active': switch.is_active,
            'deleted_at': switch.deleted_at.isoformat() if switch.deleted_at else None,
            'groups': ', '.join(switch.groups),
            'version': switch.version,
            'ttl': switch.ttl,
            'comment': switch.comment,
        }

    return switch_to_json


@pytest.fixture()
def switch_data_factory():
    def switch_data(**kwargs):
        deleted_at = factory.fuzzy.FuzzyChoice(
            [localize_datetime(factory.fuzzy.FuzzyDateTime(utc_now()).fuzz()), None],
        ).fuzz()
        return {
            'name': factory.fuzzy.FuzzyText(length=10).fuzz(),
            'is_active': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
            'deleted_at': deleted_at,
            'is_hidden': bool(deleted_at),
            'groups': (
                factory.fuzzy.FuzzyText(length=5).fuzz(), factory.fuzzy.FuzzyText(length=5).fuzz(),
            ),
            'version': factory.fuzzy.FuzzyInteger(low=0, high=100).fuzz(),
            'ttl': factory.fuzzy.FuzzyInteger(low=0, high=100).fuzz(),
            'comment': 'This is the story of a big bad wolf an little girl whose name was...',
            **kwargs,
        }

    return switch_data


@pytest.fixture()
def create_switch_data_factory(switch_data_factory):
    def switch_data(**kwargs):
        data = switch_data_factory()
        data['groups'] = ', '.join(data['groups'])
        deleted_at = data.pop('deleted_at')
        if deleted_at:
            data['deleted_at'] = deleted_at.isoformat()
        del data['is_hidden']
        data.update(kwargs)
        return data

    return switch_data


@pytest.fixture()
async def switch_factory(loop, setup_tables: Callable, switch_data_factory) -> Callable:
    engine = get_engine(settings.database_dsn)

    async def _with_params(**kwargs) -> list:
        switch_params = switch_data_factory(**kwargs)

        with engine.connect() as conn:
            conn.execute(switches.insert(), switch_params)
            query = switches.select(switches.c.name == switch_params['name'])
            return conn.execute(query).fetchone()

    return _with_params


@pytest.fixture()
async def switches_factory(setup_tables: Callable, switch_data_factory) -> Callable:
    engine = get_engine(settings.database_dsn)
    session = Session(engine)

    async def _with_params(batch_size: int = 1, **kwargs) -> list:
        switches_list = [switch_data_factory(**kwargs) for _ in range(0, batch_size)]

        with engine.connect() as conn:
            conn.execute(switches.insert(), switches_list)
            return session.query(switches).all()

    return _with_params


@pytest.fixture()
def badge_mask_id_patch(mocker):
    # anybadge increments mask_id for each badge to prevent
    # SVG <mask id="..."> duplicates
    # set it to 1 just to compare two SVG images without regard to anybadge internal details.

    return mocker.patch.object(
        Badge,
        '_get_next_mask_str',
        return_value=f'{MASK_ID_PREFIX}_1',
    )


@pytest.fixture()
def login_path():
    return '/zbs/login'
