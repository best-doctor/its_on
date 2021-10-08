import functools
import json
from typing import List, Dict

from aiocache import cached
from aiohttp import web
from aiohttp_apispec import request_schema, response_schema, docs
from aiohttp_cors import CorsViewMixin
from dynaconf import settings
from sqlalchemy.sql import and_, true, false, Select

from its_on.cache import switch_list_cache_key_builder
from its_on.models import switches
from its_on.schemes import (
    SwitchListRequestSchema, SwitchListResponseSchema, SwitchFullListResponseSchema,
)
from its_on.utils import DateTimeJSONEncoder


class SwitchListView(CorsViewMixin, web.View):
    @docs(
        summary='List of active flags for the group.',
        description='Returns a list of active flags for the passed group.',
    )
    @request_schema(SwitchListRequestSchema(), locations=['query'])
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

    def filter_active(self, queryset: Select) -> Select:
        return queryset.where(switches.c.is_active == true())

    def filter_group(self, queryset: Select, group_name: str) -> Select:
        return queryset.where(switches.c.groups.contains(f'{{{group_name}}}'))

    def filter_hidden(self, queryset: Select) -> Select:
        return queryset.where(switches.c.is_hidden == false())

    def filter_version(self, queryset: Select, version: str) -> Select:
        if version is not None:
            queryset = queryset.where(switches.c.version <= version)
        return queryset

    async def filter_queryset(self, queryset: Select) -> Select:
        validated_data = self.request['validated_data']
        group_name = validated_data['group']
        version = validated_data.get('version')

        queryset = self.filter_group(queryset, group_name)
        queryset = self.filter_active(queryset)
        queryset = self.filter_hidden(queryset)
        queryset = self.filter_version(queryset, version)

        return queryset


class SwitchOffListView(SwitchListView):
    @docs(
        summary='List of inactive flags for the group.',
        description='Returns a list of inactive flags for the passed group.',
    )
    def filter_active(self, queryset: Select) -> Select:
        return queryset.where(switches.c.is_active == false())


class SwitchFullListView(CorsViewMixin, web.View):
    @docs(
        summary='List of all active flags with full info.',
        description='Returns a list of all active flags with all necessary info for recreation.',
    )
    @response_schema(SwitchFullListResponseSchema(), 200)
    async def get(self) -> web.Response:
        data = await self.get_response_data()
        return web.json_response(data, dumps=functools.partial(json.dumps, cls=DateTimeJSONEncoder))

    async def get_response_data(self) -> Dict:
        objects = await self.load_objects()
        data = [
            {
                'name': obj.name,
                'is_active': obj.is_active,
                'is_hidden': obj.is_hidden,
                'groups': obj.groups,
                'version': obj.version,
                'comment': obj.comment,
                'ttl': obj.ttl,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at,
            }
            for obj in objects
        ]
        return {
            'result': data,
        }

    async def load_objects(self) -> List:
        async with self.request.app['db'].acquire() as conn:
            queryset = self.get_queryset()
            result = await conn.execute(queryset)
            return await result.fetchall()

    def get_queryset(self) -> Select:
        return switches.select()
