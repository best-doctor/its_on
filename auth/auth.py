from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Union

import aiohttp_jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPFound
from aiohttp_security import remember
from aiopg.sa.engine import Engine
from aiopg.sa.result import RowProxy
from aiohttp.web import Application
from aiohttp_security.abc import AbstractAuthorizationPolicy
from dynaconf import settings
from passlib.hash import sha256_crypt
from sqlalchemy import and_, func, not_

from auth import models

if TYPE_CHECKING:
    from typing import Optional


async def get_login_context(error: str | None = None) -> Dict[str, Union[str | bool]]:
    use_oauth = getattr(getattr(settings, 'OAUTH', None), 'IS_USED', False)
    only_oauth = getattr(getattr(settings, 'OAUTH', None), 'ONLY_OAUTH', False)
    context = {'context': '', 'use_oauth': use_oauth, 'only_oauth': only_oauth}
    if error:
        context['error'] = error
    return context


async def oauth_on_login(request: web.Request, user_data: dict) -> web.Response:
    await remember(request, HTTPFound('/zbs/switches'), 'admin')
    return HTTPFound('/zbs/switches')


@aiohttp_jinja2.template('users/login.html')
async def oauth_on_error(request: web.Request) -> Dict[str, Union[str | bool]]:
    return await get_login_context(error='OAUTH failed')


async def check_credentials(db_engine: Engine, username: str, password: str) -> bool:
    """Производит аутентификацию пользователя."""
    async with db_engine.acquire() as conn:
        where = and_(
            models.users.c.login == username,
        )

        query = models.users.select().where(where)
        result = await conn.execute(query)
        user = await result.fetchone()

        if user is not None:
            password_hash = user.passwd
            return sha256_crypt.verify(password, password_hash)

    return False


class DBAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, app: Application) -> None:
        self.app: Application = app

    async def authorized_userid(self, identity: str) -> Optional[str]:
        if self.app.get('db') is None:
            return None

        if await self._is_authorised(identity):
            return identity

        return None

    async def permits(self, identity: str, permission: str) -> None:
        """Нужно для имплементации абстрактного метода."""
        pass

    async def _is_authorised(self, identity: str) -> RowProxy:
        async with self.app['db'].acquire() as conn:
            where = and_(
                models.users.c.login == identity,
                not_(models.users.c.disabled),
            )
            query = models.users.select().where(where).with_only_columns([func.count()])
            return await conn.scalar(query)
