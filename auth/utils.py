from aiohttp import web
from aiohttp_security.api import authorized_userid
from sqlalchemy import and_, func

from auth.models import permissions, users
from auth.enums import Permission
from its_on.app_keys import db_key


async def get_current_user(request: web.Request) -> users:
    async with request.app[db_key].acquire() as conn:
        user_login = await authorized_userid(request)

        query = users.select().where(users.c.login == user_login)
        result = await conn.execute(query)

        user = await result.fetchone()
        return user


async def is_superuser(request: web.Request) -> bool:
    user = await get_current_user(request)
    return user.is_superuser


async def user_has_permission(request: web.Request, permission: Permission) -> bool:
    async with request.app[db_key].acquire() as conn:
        user_login = await authorized_userid(request)
        if user_login is None:
            return False

        user_query = users.select().where(users.c.login == user_login)
        user_result = await conn.execute(user_query)
        user = await user_result.fetchone()
        if user is None:
            return False

        perm_query = (
            permissions.select()
            .where(
                and_(
                    permissions.c.user_id == user.id,
                    permissions.c.perm_name == permission,
                ),
            )
            .with_only_columns(func.count())
        )
        return bool(await conn.scalar(perm_query))
