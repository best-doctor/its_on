
from typing import Dict
from urllib.parse import urlparse

from aiohttp import web
from aiopg.sa import create_engine


async def init_pg(app: web.Application) -> None:
    config = app['config']

    engine = await create_engine(
        dsn=config.DATABASE.DSN,
        echo=config.ENABLE_DB_LOGGING,
    )
    app['db'] = engine


async def close_pg(app: web.Application) -> None:
    app['db'].close()
    await app['db'].wait_closed()


def parse_dsn(dsn: str) -> Dict:
    result = urlparse(dsn)
    return {
        'drivername': result.scheme,
        'username': result.username,
        'password': result.password,
        'host': result.hostname,
        'port': result.port,
        'database': result.path.split('/', 1)[1],
    }


def make_dsn(drivername: str, username: str, password: str, host: str, port: int, database: str) -> str:
    return f'{drivername}://{username}:{password}@{host}:{port}/{database}'
