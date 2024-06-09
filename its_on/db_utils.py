from aiohttp import web
from aiopg.sa import create_engine
from pydantic import PostgresDsn


async def init_pg(app: web.Application) -> None:
    config = app['config']

    engine = await create_engine(
        dsn=str(config.database_dsn),
        echo=config.enable_db_logging,
    )
    app['db'] = engine


async def close_pg(app: web.Application) -> None:
    app['db'].close()
    await app['db'].wait_closed()


def db_name_from_dsn(dsn: PostgresDsn) -> str:
    return dsn.path.split('/')[1]
