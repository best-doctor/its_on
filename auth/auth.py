from typing import Optional

from aiopg.sa.engine import Engine
import sqlalchemy as sa
from aiohttp.web import Application
from aiohttp_security.abc import AbstractAuthorizationPolicy
from passlib.hash import sha256_crypt

from . import models


class DBAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, app: Application) -> None:
        self.app: Application = app

    async def authorized_userid(self, identity: str) -> Optional[str]:
        if self.app.get('db') is None:
            return None

        async with self.app['db'].acquire() as conn:
            where = sa.and_(
                models.users.c.login == identity,
                sa.not_(models.users.c.disabled),
            )
            query = models.users.count().where(where)
            ret = await conn.scalar(query)

            if ret:
                return identity
            else:
                return None

    async def permits(self, identity: str, permission: str) -> None:
        """Нужно для имплементации абстрактного метода."""
        pass


async def check_credentials(db_engine: Engine, username: str, password: str) -> bool:
    async with db_engine.acquire() as conn:
        where = sa.and_(models.users.c.login == username,
                        sa.not_(models.users.c.disabled))
        query = models.users.select().where(where)
        ret = await conn.execute(query)
        user = await ret.fetchone()

        if user is not None:
            password_hash = user[2]
            return sha256_crypt.verify(password, password_hash)
    return False
