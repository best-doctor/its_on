from typing import Optional
import logging
import pathlib

from aiohttp import web
from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy
import aiohttp_cors
import aiohttp_jinja2
import jinja2
from aiohttp_apispec import setup_aiohttp_apispec
import redis.asyncio as aioredis
from aiohttp_session import setup
from aiohttp_session.redis_storage import RedisStorage
from its_on.config import settings
import uvloop

from auth.auth import DBAuthorizationPolicy
from its_on.app_keys import config_key
from its_on.cache import setup_cache
from its_on.db_utils import init_pg, close_pg
from its_on.middlewares import setup_middlewares
from its_on.routes import setup_routes

BASE_DIR = pathlib.Path(__file__).parent.parent


async def init_gunicorn_app() -> web.Application:
    return await init_app()


async def make_redis_client() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=1)


async def init_app(
    redis_client: Optional[aioredis.Redis] = None,
) -> web.Application:
    app = web.Application()

    app[config_key] = settings

    if not redis_client:
        redis_client = await make_redis_client()

    storage = RedisStorage(redis_client, cookie_name='sessionid')
    setup(app, storage)

    async def dispose_redis_client(app: web.Application) -> None:
        if redis_client is not None:
            await redis_client.aclose()

    jinja2_env = aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(
            str(BASE_DIR / 'its_on' / 'templates'),
        ),
        enable_async=True,
    )

    jinja2_env.globals.update({
        'show_env_notice': settings.ENVIRONMENT_NOTICE.SHOW,
        'env_notice_name': settings.ENVIRONMENT_NOTICE.ENVIRONMENT_NAME,
        'env_notice_background_color': settings.ENVIRONMENT_NOTICE.BACKGROUND_COLOR,
    })

    app[aiohttp_jinja2.static_root_key] = '/static'

    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)
    app.on_cleanup.append(dispose_redis_client)

    setup_security(app,
                   SessionIdentityPolicy(session_key='sessionkey'),
                   DBAuthorizationPolicy(app))

    cors_config = {
        origin: aiohttp_cors.ResourceOptions(
            allow_methods=['GET', 'OPTIONS'], allow_headers=settings.CORS_ALLOW_HEADERS)
        for origin in settings.CORS_ALLOW_ORIGIN
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
    uvloop.install()
    web.run_app(init_app(), host=settings.HOST, port=settings.PORT)


if __name__ == '__main__':
    main()
