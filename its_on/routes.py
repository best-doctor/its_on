from __future__ import annotations
from typing import TYPE_CHECKING

from aiohttp import web
from dynaconf import settings

from auth.views import LoginView, LogoutView
from its_on.views import SwitchListView
from its_on.admin.views.switches import (
    SwitchListAdminView, SwitchDetailAdminView, SwitchDeleteAdminView, SwitchResurrectAdminView, SwitchAddAdminView)
from its_on.admin.views.users import (
    UserDetailAdminView, UserListAdminView,
)

if TYPE_CHECKING:
    from pathlib import Path


def setup_routes(app: web.Application, base_dir: Path) -> None:
    app.router.add_view('/zbs/login', LoginView)
    app.router.add_view('/zbs/logout', LogoutView)
    app.router.add_view('/api/v1/switch', SwitchListView)
    app.router.add_view('/zbs/switches', SwitchListAdminView, name='switches_list')
    app.router.add_view('/zbs/switches/add', SwitchAddAdminView, name='switches_add')
    app.router.add_view('/zbs/switches/{id}', SwitchDetailAdminView, name='switch_detail')
    app.router.add_view('/zbs/switches/{id}/delete', SwitchDeleteAdminView)
    app.router.add_view('/zbs/switches/{id}/resurrect', SwitchResurrectAdminView)
    app.router.add_view('/zbs/users', UserListAdminView)
    app.router.add_view('/zbs/users/{id}', UserDetailAdminView)

    if settings.ENVIRONMENT == 'Dev':
        app.router.add_static('/static', str(base_dir / 'its_on' / 'static'))
