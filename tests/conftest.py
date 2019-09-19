import pytest
from typing import Callable, Generator

from its_on.main import init_app
from its_on.settings import get_config
from .helpers import (setup_db, teardown_db, create_tables, drop_tables, create_sample_data)


@pytest.fixture
async def client(aiohttp_client: Callable) -> None:
    return await aiohttp_client(init_app)


@pytest.fixture(scope='session')
def database() -> Generator:
    config = get_config()
    setup_db(config=config)
    yield
    teardown_db(config=config)


@pytest.fixture(scope='function')
def tables_and_data(database: Callable) -> Generator:
    config = get_config()

    create_tables(config=config)
    create_sample_data(config=config)

    yield

    drop_tables(config=config)
