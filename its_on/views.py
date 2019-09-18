from aiohttp import web
from sqlalchemy.sql import and_, true

from its_on.db import switches


class SwitchListView(web.View):
    async def get(self) -> web.Response:
        async with self.request.app['db'].acquire() as conn:
            group_name = self.request.match_info.get('group_name')
            result = await conn.execute(
                (
                    switches.select()
                    .where(
                        and_(
                            switches.c.group == group_name, switches.c.is_active == true(),
                        ),
                    )
                    .order_by(switches.c.name)
                ),
            )
            switch_records = await result.fetchall()
            data = [switch.name for switch in switch_records]
            return web.json_response(data)
