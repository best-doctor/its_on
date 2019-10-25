from typing import Dict, List, Optional, Any

from aiopg.sa.result import RowProxy
import aiohttp_jinja2
from aiohttp import web
from auth.decorators import login_required
from its_on.models import switches
from marshmallow.exceptions import ValidationError
import psycopg2
from sqlalchemy.sql import false, Select

from its_on.admin.mixins import GetObjectMixin, CreateMixin, UpdateMixin
from its_on.admin.schemes import SwitchDetailAdminPostRequestSchema, SwitchAddAdminPostRequestSchema
from its_on.admin.permissions import CanEditSwitch


class SwitchListAdminView(web.View):
    model = switches

    @aiohttp_jinja2.template('switches/index.html')
    @login_required
    async def get(self) -> Dict[str, Optional[List[RowProxy]]]:
        flags = await self.get_response_data()
        return {'flags': flags}

    async def get_response_data(self) -> List[RowProxy]:
        objects = await self.load_objects()
        return objects

    async def load_objects(self) -> List:
        async with self.request.app['db'].acquire() as conn:
            queryset = self.get_queryset()
            result = await conn.execute(queryset)
            return await result.fetchall()

    def get_queryset(self) -> Select:
        return switches.select(whereclause=(switches.c.is_hidden == false()))


class SwitchDetailAdminView(web.View, UpdateMixin):
    validator = SwitchDetailAdminPostRequestSchema()
    permissions = [CanEditSwitch]
    model = switches

    async def get_context_data(self, errors: ValidationError = None, updated: bool = False) -> Dict[str, Any]:
        context_data = {
            'object': await self.get_object(self.request),
            'errors': errors,
            'updated': updated,
        }
        return context_data

    @aiohttp_jinja2.template('switches/detail.html')
    @login_required
    async def get(self) -> Dict[str, RowProxy]:
        await self._check_permissions()

        switch_object = await self.get_object(self.request)

        if switch_object.is_hidden:
            return {'object': None, 'errors': 'Oops! this switch was "deleted".'}

        return {'object': switch_object}

    @aiohttp_jinja2.template('switches/detail.html')
    @login_required
    async def post(self) -> Dict[str, Dict]:
        await self._check_permissions()

        form_data = await self.request.post()

        try:
            await self.update_object(self.request, form_data)
        except ValidationError as error:
            return await self.get_context_data(errors=error)

        return await self.get_context_data(updated=True)

    async def _check_permissions(self) -> None:
        object_to_check = await self.get_object(self.request)

        for permission in self.permissions:
            if not await permission.is_allowed(self.request, object_to_check):
                raise web.HTTPForbidden


class SwitchAddAdminView(web.View, CreateMixin):
    validator = SwitchAddAdminPostRequestSchema()
    model = switches

    async def get_context_data(self, errors: ValidationError = None, user_input: Dict = None) -> Dict[str, Any]:
        context_data = {
            'errors': errors,
        }
        if user_input:
            context_data.update(user_input)
        return context_data

    @aiohttp_jinja2.template('switches/add.html')
    @login_required
    async def get(self) -> Dict[str, RowProxy]:
        return await self.get_context_data()

    @aiohttp_jinja2.template('switches/add.html')
    @login_required
    async def post(self) -> Dict[str, Dict]:
        form_data = await self.request.post()

        try:
            await self.create_object(self.request, form_data)
        except (ValidationError, psycopg2.IntegrityError) as error:
            return await self.get_context_data(errors=error, user_input=dict(form_data))

        location = self.request.app.router['switches_list'].url_for()
        raise web.HTTPFound(location=location)


class SwitchDeleteAdminView(web.View, GetObjectMixin):
    model = switches

    @login_required
    async def get(self) -> None:
        async with self.request.app['db'].acquire() as conn:
            object_pk = await self.get_object_pk(self.request)
            update_query = self.model.update().where(self.model.c.id == object_pk).values({'is_hidden': True})

            await conn.execute(update_query)
        location = self.request.app.router['switches_list'].url_for()
        raise web.HTTPFound(location=location)


class SwitchResurrectAdminView(web.View, GetObjectMixin):
    model = switches

    @login_required
    async def get(self) -> None:
        async with self.request.app['db'].acquire() as conn:
            object_pk = await self.get_object_pk(self.request)
            update_query = self.model.update().where(self.model.c.id == object_pk).values({'is_hidden': False})

            await conn.execute(update_query)

        location = self.request.app.router['switch_detail'].url_for(id=object_pk)
        raise web.HTTPFound(location=location)
