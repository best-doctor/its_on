from aiohttp import web

from auth.views import LoginView, LogoutView
from its_on.views import SwitchListView
from its_on.admin.views import SwitchListAdminView, SwitchDetailAdminView


def setup_routes(app: web.Application) -> None:
    app.router.add_view('/zbs', LoginView)
    app.router.add_view('/logout', LogoutView)
    app.router.add_view('/api/v1/switch', SwitchListView)
    app.router.add_view('/admin/switches', SwitchListAdminView)
    app.router.add_view('/admin/switches/{id}', SwitchDetailAdminView)
