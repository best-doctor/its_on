from __future__ import annotations

from aiohttp import web
from sqlalchemy import text

from its_on.app_keys import db_key

_PROBE_ALLOW = 'GET, OPTIONS'


def _probe_options_response() -> web.Response:
    return web.Response(status=204, headers={'Allow': _PROBE_ALLOW})


async def is_app_healthy(request: web.Request) -> bool:
    try:
        async with request.app[db_key].acquire() as conn:
            await conn.execute(text('SELECT 1'))
    except Exception:  # noqa: B902
        return False
    return True


async def startup_probe(request: web.Request) -> web.Response:
    if request.method == 'OPTIONS':
        return _probe_options_response()
    return web.Response(text='ok', status=200)


async def readiness_probe(request: web.Request) -> web.Response:
    if request.method == 'OPTIONS':
        return _probe_options_response()
    if await is_app_healthy(request):
        return web.Response(text='ok', status=200)
    return web.Response(text='error', status=500)


async def liveness_probe(request: web.Request) -> web.Response:
    if request.method == 'OPTIONS':
        return _probe_options_response()
    return web.Response(text='ok', status=200)
