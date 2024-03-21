import datetime
from typing import List, Dict

from aiohttp import web
from aiopg.sa.result import RowProxy
from sqlalchemy.sql import select

from auth.models import users
from auth.utils import get_current_user
from its_on.models import switch_history, switches


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


async def save_switch_history(request: web.Request, switch: switches, new_value: str) -> None:
    async with request.app['db'].acquire() as conn:
        user = await get_current_user(request)
        create_query = switch_history.insert().values(
            switch_id=switch.id,
            user_id=user.id,
            new_value=new_value,
        )

        await conn.execute(create_query)


async def get_switch_history(request: web.Request, switch: switches) -> List[RowProxy]:
    async with request.app['db'].acquire() as conn:
        query = switch_history.select(
            whereclause=(switch_history.c.switch_id == switch.id),
        ).order_by(switch_history.c.changed_at.desc())
        result = await conn.execute(query)
        return await result.fetchall()


def annotate_switch_with_expiration_date(switch: switches) -> Dict:
    if switch.is_active:
        expires_at = switch.updated_at + datetime.timedelta(days=switch.ttl)
    else:
        expires_at = None
    return {**dict(switch), 'expires_at': expires_at}
