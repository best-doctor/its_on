from aiohttp import web
from aiopg.sa import create_engine
import sqlalchemy as sa


metadata = sa.MetaData()


switches = sa.Table(
    'switches', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('is_active', sa.Boolean, default=True),
    sa.Column('name', sa.String(255), unique=True),
    sa.Column('group', sa.String(255)),
    sa.Column('version', sa.Integer, nullable=True),
    sa.Column('comment', sa.Text),
)


class RecordNotFound(Exception):
    pass


async def init_pg(app: web.Application) -> None:
    conf = app['config']['postgres']
    engine = await create_engine(
        database=conf['name'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
    )
    app['db'] = engine


async def close_pg(app: web.Application) -> None:
    app['db'].close()
    await app['db'].wait_closed()
