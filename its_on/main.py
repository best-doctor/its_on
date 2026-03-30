from typing import Optional
import logging
import pathlib

from aiohttp import web, ClientSession
from aiohttp_oauth2 import oauth2_app
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

from auth.auth import DBAuthorizationPolicy, oauth_on_login, oauth_on_error
from its_on.app_keys import (
    client_session_key, config_key,
    oauth_auth_extras_key, oauth_authorize_url_key, oauth_client_id_key, oauth_scopes_key,
)
from its_on.cache import setup_cache
from its_on.db_utils import init_pg, close_pg
from its_on.middlewares import setup_middlewares
from its_on.routes import setup_routes, setup_oauth_route

BASE_DIR = pathlib.Path(__file__).parent.parent


async def init_gunicorn_app() -> web.Application:
    return await init_app()


async def make_redis_client() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=1)


async def client_session(app: web.Application):  # type:ignore
    async with ClientSession() as session:
        app[client_session_key] = session
        yield


async def init_app(
    redis_client: Optional[aioredis.Redis] = None,
) -> web.Application:
    app = web.Application()

    if settings.OAUTH.IS_USED:
        client_id = settings.OAUTH.CLIENT_ID
        authorize_url = settings.OAUTH.AUTHORIZE_URL
        scopes = None
        auth_extras = None
        app[oauth_client_id_key] = client_id
        app[oauth_authorize_url_key] = authorize_url
        app[oauth_scopes_key] = scopes
        app[oauth_auth_extras_key] = auth_extras or {}
        app.cleanup_ctx.append(client_session)
        setup_oauth_route(app)
        app.add_subapp(
            '/oauth/',
            oauth2_app(
                client_id=settings.OAUTH.CLIENT_ID,
                client_secret=settings.OAUTH.CLIENT_SECRET,
                authorize_url=settings.OAUTH.AUTHORIZE_URL,
                token_url=settings.OAUTH.TOKEN_URL,
                on_login=oauth_on_login,
                on_error=oauth_on_error,
                json_data=False,
            ),
        )

    app[config_key] = settings

    if not redis_client:
        redis_client = await make_redis_client()

    storage = RedisStorage(redis_client, cookie_name='sesssionid')
    setup(app, storage)

    async def dispose_redis_client(app: web.Application) -> None:
        if redis_client is not None:
            await redis_client.aclose()

    jinja2_env = aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(
            str(BASE_DIR / 'its_on' / 'templates'),
        ),
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
