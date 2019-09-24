from typing import List, Dict

from aiocache import cached
from aiohttp import web
from aiohttp_apispec import request_schema, response_schema, docs
from dynaconf import settings
from sqlalchemy.sql import and_, true, Select

from its_on.cache import switch_list_cache_key_builder
from its_on.models import switches
from its_on.schemes import SwitchListRequestSchema, SwitchListResponseSchema


class SwitchListView(web.View):
    @docs(
        summary="Список активных флагов группы.",
        description="Возвращает список активных флагов для переданной группы.",
    )
    @request_schema(SwitchListRequestSchema(strict=True), locations=['headers'])
    @response_schema(SwitchListResponseSchema(), 200)
    async def get(self) -> web.Response:
        data = await self.get_response_data()
        return web.json_response(data)

    @cached(ttl=settings.CACHE_TTL, key_builder=switch_list_cache_key_builder)
    async def get_response_data(self) -> Dict:
        objects = await self.load_objects()
        data = [obj.name for obj in objects]
        return {
            'count': len(data),
            'result': data,
        }

    async def load_objects(self) -> List:
        async with self.request.app['db'].acquire() as conn:
            queryset = await self.get_queryset()
            result = await conn.execute(queryset)
            return await result.fetchall()

    async def get_queryset(self) -> Select:
        qs = switches.select().with_only_columns([switches.c.name]).order_by(switches.c.name)
        return await self.filter_queryset(qs)

    async def filter_queryset(self, queryset: Select) -> Select:
        validated_data = self.request['validated_data']
        group_name = validated_data['group']
        version = validated_data.get('version')

        filters = [
            switches.c.group == group_name,
            switches.c.is_active == true(),
        ]
        if version is not None:
            filters.append(switches.c.version <= version)

        return queryset.where(and_(*filters))
