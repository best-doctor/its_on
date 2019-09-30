from typing import Dict, Union

from sqlalchemy.engine import ResultProxy
from sqlalchemy import Table
from aiohttp.web import Request
from marshmallow import Schema
from multidict import MultiDictProxy


class UpdateMixin:
    model: Table
    validator: Schema

    async def get_object_pk(self, request: Request) -> int:
        return request.match_info.get('id')

    async def get_object(self, request: Request) -> ResultProxy:
        async with request.app['db'].acquire() as conn:
            object_id = await self.get_object_pk(request)
            query = self.model.select(self.model.c.id == object_id)

            result = await conn.execute(query)
            return await result.fetchone()

    async def update_object(self, request: Request, to_update: MultiDictProxy) -> None:
        validated_data = self._validate_form_data(to_update)

        await self._update(request, validated_data)

    async def _update(self, request: Request, to_update: Dict[str, Union[str, bool, int]]) -> None:
        async with request.app['db'].acquire() as conn:
            object_pk = await self.get_object_pk(request)
            update_query = self.model.update().where(self.model.c.id == object_pk).values(to_update)

            await conn.execute(update_query)

    def _validate_form_data(self, to_validate: MultiDictProxy) -> Dict[str, Union[int, str, bool]]:
        return self.validator.load(to_validate)
