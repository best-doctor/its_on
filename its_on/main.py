import logging
import asyncio
import pathlib

from aiohttp import web
from aiohttp_security import setup as setup_security
from aiohttp_security import CookiesIdentityPolicy
import aiohttp_jinja2
import jinja2
from aiohttp_apispec import setup_aiohttp_apispec
from dynaconf import settings
import uvloop

from auth.auth import DBAuthorizationPolicy
from its_on.cache import setup_cache
from its_on.db_utils import init_pg, close_pg
from its_on.middlewares import setup_middlewares
from its_on.routes import setup_routes

BASE_DIR = pathlib.Path(__file__).parent.parent


async def init_app(loop: asyncio.AbstractEventLoop = None) -> web.Application:
    app = web.Application(loop=loop)

    app['config'] = settings

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(
            str(BASE_DIR / 'its_on' / 'templates'),
        ),
    )
    app['static_root_url'] = '/static'

    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)

    setup_security(app,
                   CookiesIdentityPolicy(),
                   DBAuthorizationPolicy(app))

    setup_routes(app, BASE_DIR)
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
    app = asyncio.run(init_app())
    uvloop.install()
    web.run_app(app, host=settings.HOST, port=settings.PORT)


if __name__ == '__main__':
    main()
