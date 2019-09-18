from aiohttp import web
from aiohttp_apispec import validation_middleware


def setup_middlewares(app: web.Application) -> None:
    app.middlewares.append(validation_middleware)
