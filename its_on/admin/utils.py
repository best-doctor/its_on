from typing import List

from aiohttp import web
from aiopg.sa.result import RowProxy
from sqlalchemy.sql import select

from auth.models import users
from its_on.models import switches


async def get_user_switches(request: web.Request, user: users) -> List[RowProxy]:
    async with request.app['db'].acquire() as conn:
        from its_on.models import user_switches  # Почему-то алхимия не видит этот импорт наверху

        user_switches_joined = (
            users
            .join(user_switches, users.c.id == user_switches.c.user_id)
            .join(switches, user_switches.c.switch_id == switches.c.id)
        )

        query = select([switches.c.name]).select_from(user_switches_joined).where(
            users.c.id == user.id)
        result = await conn.execute(query)
        user_switches = await result.fetchall()

        return user_switches


async def get_user_switches_names(request: web.Request, user: users) -> List[str]:
    user_switches = await get_user_switches(request, user)
    return [user_switch.name for user_switch in user_switches]
