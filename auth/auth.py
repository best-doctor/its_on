from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Union

from aiohttp.web import Application
from aiohttp_security.abc import AbstractAuthorizationPolicy
from aiopg.sa.engine import Engine
from aiopg.sa.result import RowProxy
from its_on.config import settings
from passlib.hash import sha256_crypt
from sqlalchemy import and_, func, not_

from auth import models
from auth.enums import Permission
from its_on.app_keys import db_key

if TYPE_CHECKING:
    from typing import Optional


async def get_login_context(error: str | None = None) -> Dict[str, Union[str | bool]]:
    use_oauth = getattr(getattr(settings, 'OAUTH', None), 'IS_ENABLED', False)
    oauth_sign_in_title = getattr(getattr(settings, 'OAUTH', None), 'SIGN_IN_TITLE', '')
    context = {
        'context': '',
        'use_oauth': use_oauth,
        'only_oauth': use_oauth,
        'oauth_sign_in_title': oauth_sign_in_title,
    }
    if error:
        context['error'] = error
    return context


async def check_credentials(db_engine: Engine, username: str, password: str) -> bool:
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


async def get_or_create_user(db_engine: Engine, login: str) -> RowProxy:
    async with db_engine.acquire() as conn:
        query = models.users.select().where(models.users.c.login == login)
        result = await conn.execute(query)
        user = await result.fetchone()

        if user is not None:
            return user

        unusable_password = sha256_crypt.hash('!')
        insert_query = models.users.insert().values(
            login=login,
            passwd=unusable_password,
            is_superuser=False,
            disabled=False,
        )
        await conn.execute(insert_query)

        result = await conn.execute(query)
        user = await result.fetchone()
        await conn.execute(
            models.permissions.insert().values(
                user_id=user.id,
                perm_name=Permission.SWITCHES_EDIT_ALL,
            ),
        )
        return user


class DBAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, app: Application) -> None:
        self.app: Application = app

    async def authorized_userid(self, identity: str) -> Optional[str]:
        if self.app.get(db_key) is None:
            return None

        if await self._is_authorised(identity):
            return identity

        return None

    async def permits(
        self, identity: str | None, permission: str | Enum, context: Any = None,
    ) -> bool:
        return True

    async def _is_authorised(self, identity: str) -> RowProxy:
        async with self.app[db_key].acquire() as conn:
            where = and_(
                models.users.c.login == identity,
                not_(models.users.c.disabled),
            )
            query = models.users.select().where(where).with_only_columns(func.count())
            return await conn.scalar(query)
