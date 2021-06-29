from typing import Any, Dict, List, Optional, Union

import aiohttp_jinja2
import psycopg2
from aiohttp import ClientSession
from aiohttp import web
from aiopg.sa.result import RowProxy
from dynaconf import settings
from marshmallow.exceptions import ValidationError
from multidict import MultiDictProxy
from sqlalchemy.sql import Select, false

from auth.decorators import login_required
from its_on.admin.mixins import CreateMixin, GetObjectMixin, UpdateMixin
from its_on.admin.permissions import CanEditSwitch
from its_on.admin.schemes import (
    SwitchAddAdminPostRequestSchema,
    SwitchCopyFromAnotherItsOnAdminPostRequestSchema,
    SwitchDetailAdminPostRequestSchema,
    SwitchListAdminRequestSchema,
)
from its_on.admin.utils import get_switch_history, save_switch_history
from its_on.models import switches


class SwitchListAdminView(web.View):
    model = switches
    validator = SwitchListAdminRequestSchema()

    @aiohttp_jinja2.template('switches/index.html')
    @login_required
    async def get(self) -> Dict[str, Union[Optional[List[RowProxy]], bool]]:
        request_params = self.validator.load(data=self.request.query)
        flags = await self.get_response_data(request_params)
        groups = await self.get_distinct_groups(request_params)
        return {
            'active_group': request_params.get('group'),
            'flags': flags,
            'groups': groups,
            'show_copy_button': bool(settings.SYNC_FROM_ITS_ON_URL),
        }

    async def get_response_data(self, request_params: Dict[str, Any]) -> List:
        async with self.request.app['db'].acquire() as conn:
            queryset = self.filter_queryset(self.get_queryset(), request_params)
            result = await conn.execute(queryset)
            return await result.fetchall()

    async def get_distinct_groups(self, request_params: Dict[str, Any]) -> List[str]:
        async with self.request.app['db'].acquire() as conn:
            queryset = self.filter_hidden(self.get_queryset(), request_params)
            result = await conn.execute(queryset)
            flags = await result.fetchall()
            return sorted({group for flag in flags for group in flag.groups})

    def get_queryset(self) -> Select:
        return switches.select()

    def order_queryset(self, qs: Select, request_params: Dict[str, Any]) -> Select:
        # Default ordering
        return qs.order_by(switches.c.created_at.desc())

    def filter_hidden(self, qs: Select, request_params: Dict[str, Any]) -> Select:
        if not request_params.get('show_hidden'):
            qs = qs.where(switches.c.is_hidden == false())
        return qs

    def filter_group(self, qs: Select, request_params: Dict[str, Any]) -> Select:
        group = request_params.get('group')
        if group:
            qs = qs.where(switches.c.groups.any(group))
        return qs

    def filter_queryset(self, qs: Select, request_params: Dict[str, Any]) -> Select:
        qs = self.filter_hidden(qs, request_params)
        qs = self.filter_group(qs, request_params)
        return self.order_queryset(qs, request_params)


class SwitchDetailAdminView(web.View, UpdateMixin):
    validator = SwitchDetailAdminPostRequestSchema()
    permissions = [CanEditSwitch]
    model = switches

    async def get_context_data(
        self, switch: Optional[RowProxy] = None, errors: ValidationError = None, updated: bool = False,
    ) -> Dict[str, Any]:
        switch = switch if switch else await self.get_object(self.request)
        switch_history = await get_switch_history(self.request, switch)
        context_data = {
            'object': switch,
            'switch_history': switch_history,
            'errors': errors,
            'updated': updated,
        }
        return context_data

    @aiohttp_jinja2.template('switches/detail.html')
    @login_required
    async def get(self) -> Dict[str, Any]:
        await self._check_permissions()

        switch_object = await self.get_object(self.request)

        if switch_object.is_hidden:
            return {'object': None, 'errors': 'Oops! this switch was "deleted".'}

        return await self.get_context_data(switch=switch_object)

    @aiohttp_jinja2.template('switches/detail.html')
    @login_required
    async def post(self) -> Dict[str, Dict]:
        await self._check_permissions()

        form_data = await self.request.post()

        try:
            await self.update_object(self.request, form_data)
        except ValidationError as error:
            return await self.get_context_data(errors=error)

        switch_object = await self.get_object(self.request)
        new_value = str(form_data.get('is_active'))
        await save_switch_history(self.request, switch_object, new_value)

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

    async def resurrect_deleted_flag(self, form_data: MultiDictProxy) -> Optional[Dict[str, Any]]:
        async with self.request.app['db'].acquire() as conn:
            result = await conn.execute(
                switches.select().where(switches.c.name == form_data['name']))
            already_created_switch = await result.first()

            if already_created_switch:
                try:
                    form_data = self._validate_form_data(form_data)  # type: ignore
                except ValidationError as error:
                    return await self.get_context_data(errors=error, user_input=dict(form_data))
                form_data['is_hidden'] = False  # type: ignore
                update_query = self.model.update().where(
                    self.model.c.id == str(already_created_switch.id)).values(
                    form_data)
                await conn.execute(update_query)

                new_value = str(form_data.get('is_active'))
                await save_switch_history(self.request, already_created_switch, new_value)

                location = self.request.app.router['switches_list'].url_for()
                raise web.HTTPFound(location=location)

    @aiohttp_jinja2.template('switches/add.html')
    @login_required
    async def get(self) -> Dict[str, RowProxy]:
        return await self.get_context_data()

    @aiohttp_jinja2.template('switches/add.html')
    @login_required
    async def post(self) -> Dict[str, Dict]:
        form_data = await self.request.post()

        resurrect_deleted_flag_raised_error = await self.resurrect_deleted_flag(form_data=form_data)
        if resurrect_deleted_flag_raised_error is not None:
            return resurrect_deleted_flag_raised_error

        try:
            await self.create_object(self.request, form_data)
        except (ValidationError, psycopg2.IntegrityError) as error:
            return await self.get_context_data(errors=error, user_input=dict(form_data))

        location = self.request.app.router['switches_list'].url_for()
        raise web.HTTPFound(location=location)


class SwitchesCopyAdminView(web.View, CreateMixin):
    validator = SwitchCopyFromAnotherItsOnAdminPostRequestSchema()
    model = switches

    @staticmethod
    async def _get_switches_data() -> MultiDictProxy:
        async with ClientSession() as session:
            async with session.get(settings.SYNC_FROM_ITS_ON_URL) as resp:
                return await resp.json()

    @login_required
    async def post(self) -> None:
        update_existing = bool(self.request.rel_url.query.get('update_existing'))
        switches_data = await self._get_switches_data()
        for switch_data in switches_data['result']:
            await self._create_or_update_switch(switch_data, update_existing)

        location = self.request.app.router['switches_list'].url_for()
        raise web.HTTPFound(location=location)

    async def _create_or_update_switch(
        self, switch_data: MultiDictProxy, update_existing: bool = False,
    ) -> None:
        try:
            await self.create_object(self.request, switch_data)
        except (ValidationError, psycopg2.IntegrityError):
            if update_existing:
                await self._update_switch(switch_data)

    async def _update_switch(self, switch_data: MultiDictProxy) -> None:
        async with self.request.app['db'].acquire() as conn:
            update_query = (
                self.model.update()
                .where(self.model.c.name == switch_data['name'])
                .values(switch_data)
            )
            try:
                await conn.execute(update_query)
            except (ValidationError, psycopg2.IntegrityError):
                pass


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
