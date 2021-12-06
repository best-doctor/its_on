import datetime
from typing import Callable, Generator
from unittest.mock import MagicMock

import pytest
import factory.fuzzy
from dynaconf import settings
from sqlalchemy.orm import Session

from its_on.main import init_gunicorn_app
from its_on.models import switches
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
def asserted_switch_full_info_data():
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


@pytest.fixture()
def switch_data_factory():
    return {
        'name': 'switch_to_check_add',
        'is_active': True,
        'groups': 'check_adding, group2,    ,,',
        'version': 1,
        'comment': 'This is the story of a big bad wolf an little girl whose name was...',
    }


@pytest.fixture(params=[True, False])
def switch_data_factory_with_ttl(request, switch_data_factory):
    switch_data = switch_data_factory
    default_ttl = settings.FLAG_TTL_DAYS
    passed_ttl = 100
    if request.param is True:
        switch_data['ttl'] = passed_ttl
        return switch_data, passed_ttl
    return switch_data, default_ttl


@pytest.fixture()
async def switch_factory(setup_tables: Callable) -> Callable:
    engine = get_engine(settings.DATABASE.DSN)
    session = Session(engine)

    async def _with_params(batch_size: int = 1) -> list:
        switches_list = [{
            'name': factory.fuzzy.FuzzyText(length=10).fuzz(),
            'is_active': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
            'is_hidden': factory.fuzzy.FuzzyChoice([True, False]).fuzz(),
            'groups': (
                factory.fuzzy.FuzzyText(length=5).fuzz(), factory.fuzzy.FuzzyText(length=5).fuzz(),
            ),
            'version': factory.fuzzy.FuzzyInteger(low=0, high=100).fuzz(),
            'jira_ticket': factory.fuzzy.FuzzyText(length=10).fuzz(),
            'ttl': factory.fuzzy.FuzzyInteger(low=0, high=100).fuzz(),
        } for _ in range(0, batch_size)]

        with engine.connect() as conn:
            conn.execute(switches.insert(), switches_list)
            return session.query(switches).all()

    return _with_params
