from typing import Callable, Generator
from unittest.mock import MagicMock

import pytest
from dynaconf import settings
from its_on.main import init_gunicorn_app
from its_on.models import switches

from .helpers import create_sample_data, create_tables, drop_tables, setup_db, teardown_db


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


@pytest.fixture()
async def client(aiohttp_client: Callable) -> None:
    app = await init_gunicorn_app()
    return await aiohttp_client(app)


@pytest.fixture()
async def switch(client):
    async with client.server.app['db'].acquire() as conn:
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
    setup_db(config=settings)
    yield
    teardown_db(config=settings)


@pytest.fixture(scope='function')
def setup_tables(setup_database: Callable) -> Generator:
    create_tables(config=settings)
    yield
    drop_tables(config=settings)


@pytest.fixture(scope='function')
def setup_tables_and_data(setup_tables: Callable) -> Generator:
    create_sample_data(config=settings)
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
            },
            {
                'name': 'switch2',
                'is_active': True,
                'is_hidden': False,
                'groups': ['group1'],
                'version': None,
                'comment': None,
            },
            {
                'name': 'switch3',
                'is_active': False,
                'is_hidden': False,
                'groups': ['group1'],
                'version': 4,
                'comment': None,
            },
            {
                'name': 'switch4',
                'is_active': True,
                'is_hidden': False,
                'groups': ['group1', 'group3'],
                'version': 4,
                'comment': None,
            },
            {
                'name': 'switch5',
                'is_active': True,
                'is_hidden': False,
                'groups': ['group2'],
                'version': 4,
                'comment': None,
            },
            {
                'name': 'switch6',
                'is_active': True,
                'is_hidden': True,
                'groups': ['group2'],
                'version': 4,
                'comment': None,
            },
            {
                'name': 'switch7',
                'is_active': True,
                'is_hidden': False,
                'groups': ['soft_delete'],
                'version': None,
                'comment': None,
            },
        ],
    }


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
                'version': None,
                'comment': None,
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
