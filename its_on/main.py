from typing import Optional
import logging
import asyncio
import pathlib

from aiohttp import web
from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy
import aiohttp_cors
import aiohttp_jinja2
import jinja2
from aiohttp_apispec import setup_aiohttp_apispec
import aioredis
from aiohttp_session import setup
from aiohttp_session.redis_storage import RedisStorage

from auth.auth import DBAuthorizationPolicy
from its_on.cache import setup_cache
from its_on.db_utils import init_pg, close_pg
from its_on.middlewares import setup_middlewares
from its_on.routes import setup_routes
from its_on.settings import settings

BASE_DIR = pathlib.Path(__file__).parent.parent


async def init_gunicorn_app() -> web.Application:
    redis_pool = await make_redis_pool()
    loop = asyncio.get_event_loop()
    return init_app(loop, redis_pool)


async def make_redis_pool() -> aioredis.ConnectionsPool:
    redis_address = str(settings.redis_url)
    return await aioredis.create_redis_pool(redis_address, timeout=1)


def init_app(
    loop: asyncio.AbstractEventLoop,
    redis_pool: Optional[aioredis.ConnectionsPool] = None,
) -> web.Application:
    app = web.Application()

    app['config'] = settings

    if not redis_pool:
        redis_pool = loop.run_until_complete(make_redis_pool())

    storage = RedisStorage(redis_pool, cookie_name='sesssionid')
    setup(app, storage)

    async def dispose_redis_pool(app: web.Application) -> None:
        if redis_pool is not None:
            redis_pool.close()
            await redis_pool.wait_closed()

    jinja2_env = aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(
            str(BASE_DIR / 'its_on' / 'templates'),
        ),
    )

    jinja2_env.globals.update({
        'show_env_notice': settings.environment_notice.show,
        'env_notice_name': settings.environment_notice.environment_name,
        'env_notice_background_color': settings.environment_notice.background_color,
    })

    app['static_root_url'] = '/static'

    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)
    app.on_cleanup.append(dispose_redis_pool)

    setup_security(app,
                   SessionIdentityPolicy(session_key='sessionkey'),
                   DBAuthorizationPolicy(app))

    cors_config = {
        origin: aiohttp_cors.ResourceOptions(
            allow_methods=['GET', 'OPTIONS'], allow_headers=settings.cors_allow_headers)
        for origin in settings.cors_allow_origin
    }
    cors = aiohttp_cors.setup(app, defaults=cors_config)

    setup_routes(app, BASE_DIR, cors)

    setup_aiohttp_apispec(
        app=app,
        title='Flags Bestdoctor',
        version='v1',
        url='/api/docs/swagger.json',
        swagger_path='/api/docs',
        static_path='/assets/swagger',
        request_data_name='validated_data')
    setup_middlewares(app)
    setup_cache(app)

    return app


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    app = init_app(loop)
    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == '__main__':
    main()
