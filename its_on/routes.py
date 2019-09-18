from aiohttp import web

from its_on.views import SwitchListView


def setup_routes(app: web.Application) -> None:
    app.router.add_view('/switch/{group_name}', SwitchListView)
