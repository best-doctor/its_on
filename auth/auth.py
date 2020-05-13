from __future__ import annotations
from typing import TYPE_CHECKING

from aiopg.sa.engine import Engine
from aiopg.sa.result import RowProxy
from aiohttp.web import Application
from aiohttp_security.abc import AbstractAuthorizationPolicy
from passlib.hash import sha256_crypt
from sqlalchemy import and_, func, not_

from auth import models

if TYPE_CHECKING:
    from typing import Optional


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
