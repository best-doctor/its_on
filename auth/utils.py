from aiohttp import web
from aiohttp_security.api import authorized_userid

from auth.models import users


async def get_current_user(request: web.Request) -> users:
    async with request.app['db'].acquire() as conn:
        user_login = await authorized_userid(request)

        query = users.select().where(users.c.login == user_login)
        result = await conn.execute(query)

        user = await result.fetchone()
        return user


async def is_superuser(request: web.Request) -> bool:
    user = await get_current_user(request)
    return user.is_superuser
