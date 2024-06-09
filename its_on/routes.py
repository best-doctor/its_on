from __future__ import annotations
from typing import TYPE_CHECKING

from aiohttp.web import Application
from aiohttp_cors import CorsConfig

from auth.views import LoginView, LogoutView
from its_on.enums import Environment
from its_on.settings import settings, app_settings
from its_on.views import SwitchFullListView, SwitchListView, SwitchSvgBadgeView
from its_on.admin.views.switches import (
    SwitchAddAdminView,
    SwitchDeleteAdminView,
    SwitchDetailAdminView,
    SwitchListAdminView,
    SwitchesCopyAdminView,
)
from its_on.admin.views.users import UserDetailAdminView, UserListAdminView

if TYPE_CHECKING:
    from pathlib import Path


def setup_routes(app: Application, base_dir: Path, cors_config: CorsConfig) -> None:
    app.router.add_view('/zbs/login', LoginView, name='login_view')
    app.router.add_view('/zbs/logout', LogoutView)
    app.router.add_view('/zbs/switches', SwitchListAdminView, name='switches_list')
    app.router.add_view('/zbs/switches/add', SwitchAddAdminView, name='switches_add')
    app.router.add_view('/zbs/switches/copy', SwitchesCopyAdminView, name='switches_copy')
    app.router.add_view('/zbs/switches/{id}', SwitchDetailAdminView, name='switch_detail')
    app.router.add_view('/zbs/switches/{id}/delete', SwitchDeleteAdminView)
    app.router.add_view('/zbs/users', UserListAdminView)
    app.router.add_view('/zbs/users/{id}', UserDetailAdminView)

    get_switch_view = app.router.add_view('/api/v1/switch', SwitchListView)
    cors_config.add(get_switch_view)

    get_switch_svg_badge_view = app.router.add_view(
        '/api/v1/switches/{id}/svg-badge',
        SwitchSvgBadgeView,
        name='switch_svg_badge',
    )
    cors_config.add(get_switch_svg_badge_view)

    if settings.enable_switches_full_info_endpoint:
        get_switch_full_view = app.router.add_view('/api/v1/switches_full_info', SwitchFullListView)
        cors_config.add(get_switch_full_view)

    if app_settings.environment is Environment.dev:
        app.router.add_static('/static', str(base_dir / 'its_on' / 'static'))
