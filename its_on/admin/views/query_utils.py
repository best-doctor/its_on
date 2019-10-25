from typing import List, Optional, Tuple

from aiohttp import web
from sqlalchemy.sql import not_, and_

from auth.models import users


async def remove_user_switches(request: web.Request, user: users, switches_ids: List[Optional[str]]) -> None:
    from its_on.models import user_switches

    async with request.app['db'].acquire() as conn:
        await conn.execute(
            user_switches.delete().where(
                and_(user_switches.c.user_id == user.id,
                     not_(user_switches.c.switch_id.in_(switches_ids))),
            ),
        )


async def is_user_switch_exist(
    request: web.Request,
    switch_id: Optional[str],
    user_id: int,
) -> List[Optional[Tuple[int, int]]]:
    from its_on.models import user_switches

    query = user_switches.select().where(
        and_(
            user_switches.c.switch_id == switch_id,
            user_switches.c.user_id == user_id,
        ),
    )

    async with request.app['db'].acquire() as conn:
        result = await conn.execute(query)
        return await result.fetchall()


async def create_new_user_switch(request: web.Request, switch_id: Optional[str], user_id: int) -> None:
    from its_on.models import user_switches

    async with request.app['db'].acquire() as conn:
        query = user_switches.insert().values(user_id=user_id, switch_id=switch_id)
        await conn.execute(query)
