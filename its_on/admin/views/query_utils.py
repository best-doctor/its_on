from typing import Dict, List, Optional, Tuple

from aiohttp import web
from aiopg.sa.result import RowProxy

from its_on.app_keys import db_key
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import not_, and_

from auth.models import users
from its_on.models import environments, switch_environments


async def remove_user_switches(request: web.Request, user: users, switches_ids: List[Optional[str]]) -> None:
    from its_on.models import user_switches

    async with request.app[db_key].acquire() as conn:
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

    async with request.app[db_key].acquire() as conn:
        result = await conn.execute(query)
        return await result.fetchall()


async def create_new_user_switch(request: web.Request, switch_id: Optional[str], user_id: int) -> None:
    from its_on.models import user_switches

    async with request.app[db_key].acquire() as conn:
        query = user_switches.insert().values(user_id=user_id, switch_id=switch_id)
        await conn.execute(query)


async def get_all_environments(request: web.Request) -> List[RowProxy]:
    async with request.app[db_key].acquire() as conn:
        result = await conn.execute(environments.select().order_by(environments.c.name))
        return await result.fetchall()


async def get_switch_environments_states(request: web.Request, switch_id: int) -> Dict[int, bool]:
    """Возвращает {environment_id: is_active} для окружений, привязанных к флагу."""
    query = switch_environments.select().where(switch_environments.c.switch_id == switch_id)

    async with request.app[db_key].acquire() as conn:
        result = await conn.execute(query)
        return {row.environment_id: row.is_active for row in await result.fetchall()}


async def sync_switch_environments(
    request: web.Request, switch_id: int, states: Dict[int, bool],
) -> None:
    """
    Приводит switch_environments флага к переданному состоянию.

    Лишние записи удаляются, недостающие добавляются, is_active существующих обновляется.
    Несуществующие в справочнике окружения игнорируются.
    """
    async with request.app[db_key].acquire() as conn:
        result = await conn.execute(
            environments.select().with_only_columns(environments.c.id).where(
                environments.c.id.in_(list(states)),
            ),
        )
        known_ids = {row.id for row in await result.fetchall()}
        states = {env_id: is_active for env_id, is_active in states.items() if env_id in known_ids}

        await conn.execute(
            switch_environments.delete().where(
                and_(
                    switch_environments.c.switch_id == switch_id,
                    not_(switch_environments.c.environment_id.in_(list(states))),
                ),
            ),
        )
        for environment_id, is_active in states.items():
            upsert = insert(switch_environments).values(
                switch_id=switch_id, environment_id=environment_id, is_active=is_active,
            )
            await conn.execute(
                upsert.on_conflict_do_update(
                    constraint='switch_environment_unique',
                    set_={'is_active': upsert.excluded.is_active},
                ),
            )
