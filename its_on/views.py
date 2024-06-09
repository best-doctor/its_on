import functools
import json
import textwrap

from aiocache import cached
from aiohttp import web
from aiohttp_apispec import request_schema, response_schema, docs
from aiohttp_cors import CorsViewMixin
from sqlalchemy.sql import Select
from typing import Dict, List, Optional

from its_on.admin.mixins import GetObjectMixin
from its_on.cache import switch_list_cache_key_builder
from its_on.models import switches
from its_on.schemes import (
    SwitchListRequestSchema, SwitchListResponseSchema, SwitchFullListResponseSchema,
)
from its_on.settings import settings
from its_on.utils import DateTimeJSONEncoder, reverse
from its_on.utils import get_switch_badge_svg, utc_now


class SwitchListView(CorsViewMixin, web.View):
    @docs(
        summary='List of active flags for the group.',
        description='Returns a list of active flags for the passed group.',
    )
    @request_schema(SwitchListRequestSchema(), locations=['query'])
    @response_schema(SwitchListResponseSchema(), code=200, description='Successful operation')
    async def get(self) -> web.Response:
        data = await self.get_response_data()
        return web.json_response(data)

    @cached(ttl=settings.cache_ttl, key_builder=switch_list_cache_key_builder)
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

    def filter_active(self, queryset: Select, is_active: bool = True) -> Select:
        return queryset.where(switches.c.is_active.is_(is_active))

    def filter_group(self, queryset: Select, group_name: str) -> Select:
        return queryset.where(switches.c.groups.any(group_name))

    def filter_hidden(self, queryset: Select) -> Select:
        return queryset.where(switches.c.deleted_at.is_(None) | (switches.c.deleted_at > utc_now()))

    def filter_version(self, queryset: Select, version: Optional[str] = None) -> Select:
        if version is not None:
            queryset = queryset.where(switches.c.version <= version)
        return queryset

    async def filter_queryset(self, queryset: Select) -> Select:
        validated_data = self.request['validated_data']

        queryset = self.filter_group(queryset, validated_data['group'])
        queryset = self.filter_active(queryset, validated_data.get('is_active', True))
        queryset = self.filter_hidden(queryset)
        queryset = self.filter_version(queryset, validated_data.get('version'))

        return queryset


class SwitchFullListView(CorsViewMixin, web.View):
    @docs(
        summary='List of all active flags with full info.',
        description='Returns a list of all active flags with all necessary info for recreation.',
    )
    @response_schema(SwitchFullListResponseSchema(), code=200, description='Successful operation')
    async def get(self) -> web.Response:
        data = await self.get_response_data()
        return web.json_response(data, dumps=functools.partial(json.dumps, cls=DateTimeJSONEncoder))

    async def get_response_data(self) -> Dict:
        objects = await self.load_objects()
        data = [
            {
                'name': obj.name,
                'is_active': obj.is_active,
                'is_hidden': bool(obj.deleted_at),
                'groups': obj.groups,
                'version': obj.version,
                'comment': obj.comment,
                'ttl': obj.ttl,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at,
                'deleted_at': obj.deleted_at,
                'flag_url': reverse(
                    request=self.request,
                    router_name='switch_detail',
                    params={'id': str(obj.id)},
                ),
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


class SwitchSvgBadgeView(CorsViewMixin, GetObjectMixin, web.View):
    model = switches

    @docs(
        summary='SVG badge with actual flag information.',
        description=textwrap.dedent(
            """
            Returns an SVG image with actual flag information:

            | State | Badge |
            |-----|-----|
            | Active flag | <img src="/static/img/active-flag-badge.svg"/> |
            | Inactive flag | <img src="/static/img/inactive-flag-badge.svg"/> |
            | Deleted flag | <img src="/static/img/deleted-flag-badge.svg"/> |
            | Unknown flag | <img src="/static/img/unknown-flag-badge.svg"/> |

            `{host}` here means a host name of the request.
            """,
        ),
        produces=['image/svg+xml'],
        responses={
            200: {
                'description': 'Successful operation',
            },
        },
    )
    async def get(self) -> web.Response:
        switch = await self.get_object(self.request)

        svg_badge = get_switch_badge_svg(self.request.host, switch)

        return web.Response(body=svg_badge, content_type='image/svg+xml')
