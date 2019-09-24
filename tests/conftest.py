import pytest
from typing import Callable, Generator

from dynaconf import settings

from its_on.main import init_app
from .helpers import (setup_db, teardown_db, create_tables, drop_tables, create_sample_data)


@pytest.fixture
async def client(aiohttp_client: Callable) -> None:
    app = await init_app()
    return await aiohttp_client(app)


@pytest.fixture(scope='session')
def database() -> Generator:
    setup_db(config=settings)
    yield
    teardown_db(config=settings)


@pytest.fixture(scope='function')
def tables_and_data(database: Callable) -> Generator:
    create_tables(config=settings)
    create_sample_data(config=settings)

    yield

    drop_tables(config=settings)
