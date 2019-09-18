from typing import List, Dict

from aiohttp import web
from aiohttp_apispec import request_schema, response_schema
from marshmallow import Schema, fields
from sqlalchemy.sql import and_, true, Select

from its_on.db import switches


class RequestSchema(Schema):
    group = fields.Str(description='group', required=True)
    version = fields.Int()


class ResponseSchema(Schema):
    count = fields.Integer()
    result = fields.List(fields.String)


class SwitchListView(web.View):
    @request_schema(RequestSchema(strict=True))
    @response_schema(ResponseSchema(), 200)
    async def get(self) -> web.Response:
        objects = await self.load_objects()
        data = await self.get_response_data(objects)
        return web.json_response(data)

    async def load_objects(self) -> List:
        async with self.request.app['db'].acquire() as conn:
            queryset = await self.get_queryset()
            result = await conn.execute(queryset)
            objects = await result.fetchall()
            return objects

    async def get_queryset(self) -> Select:
        qs = switches.select()
        qs = await self.filter_queryset(qs)
        return qs

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

    async def get_response_data(self, objects: List) -> Dict:
        data = [obj.name for obj in objects]
        return {
            'count': len(data),
            'result': data,
        }
