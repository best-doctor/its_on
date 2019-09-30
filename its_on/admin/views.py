from typing import Dict, List, Optional, Any

from aiopg.sa.result import RowProxy
import aiohttp_jinja2
from aiohttp import web
from auth.decorators import login_required
from its_on.models import switches
from marshmallow.exceptions import ValidationError
from sqlalchemy.sql import Select

from .mixins import UpdateMixin
from .schemes import SwitchDetailAdminPostRequestSchema


class SwitchListAdminView(web.View):
    model = switches

    @aiohttp_jinja2.template('index.html')
    @login_required
    async def get(self) -> Dict[str, Optional[List[RowProxy]]]:
        flags = await self.get_response_data()
        return {'flags': flags}

    async def get_response_data(self) -> List[RowProxy]:
        objects = await self.load_objects()
        return objects

    async def load_objects(self) -> List:
        async with self.request.app['db'].acquire() as conn:
            queryset = await self.get_queryset()
            result = await conn.execute(queryset)
            return await result.fetchall()

    async def get_queryset(self) -> Select:
        return switches.select()


class SwitchDetailAdminView(web.View, UpdateMixin):
    validator = SwitchDetailAdminPostRequestSchema()
    model = switches

    async def get_context_data(self, errors: ValidationError = None, updated: bool = False) -> Dict[str, Any]:
        context_data = {
            'object': await self.get_object(self.request),
            'errors': errors,
            'updated': updated,
        }
        return context_data

    @aiohttp_jinja2.template('detail.html')
    @login_required
    async def get(self) -> Dict[str, RowProxy]:
        switch_object = await self.get_object(self.request)
        return {'object': switch_object}

    @aiohttp_jinja2.template('detail.html')
    @login_required
    async def post(self) -> Dict[str, Dict]:
        form_data = await self.request.post()

        try:
            await self.update_object(self.request, form_data)
        except ValidationError as error:
            return await self.get_context_data(errors=error)

        return await self.get_context_data(updated=True)
