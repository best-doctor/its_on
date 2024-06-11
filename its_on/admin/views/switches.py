import datetime
import typing

import aiohttp_jinja2
import psycopg2
from aiohttp import ClientConnectionError, ClientResponseError, ClientSession
from aiohttp import web
from aiopg.sa.result import RowProxy
from marshmallow.exceptions import ValidationError
from multidict import MultiDictProxy
from sqlalchemy.sql import Select

from auth.decorators import login_required
from its_on.admin.mixins import CreateMixin, GetObjectMixin, UpdateMixin
from its_on.admin.permissions import CanEditSwitch
from its_on.admin.schemes import (
    SwitchAddAdminPostRequestSchema,
    SwitchCopyFromAnotherItsOnAdminPostRequestSchema,
    SwitchDetailAdminPostRequestSchema,
    SwitchListAdminRequestSchema,
)
from its_on.admin.utils import (
    annotate_switch_with_expiration_date,
    get_switch_history,
    save_switch_history,
)
from its_on.models import switches
from its_on.schemes import RemoteSwitchesDataSchema
from its_on.settings import settings
from its_on.utils import get_switch_badge_svg, get_switch_markdown_badge, utc_now


class SwitchListAdminView(web.View):
    model = switches
    validator = SwitchListAdminRequestSchema()

    @aiohttp_jinja2.template('switches/index.html')
    @login_required
    async def get(self) -> dict[str, list[RowProxy] | None | bool | list[str] | list[dict]]:
        request_params = self.validator.load(data=self.request.query)
        flags = await self.get_response_data(request_params)
        groups = await self.get_distinct_groups(request_params)
        return {
            'active_group': request_params.get('group'),
            'flags': flags,
            'groups': groups,
            'show_copy_button': bool(settings.sync_from_its_on_url),
        }

    async def get_response_data(self, request_params: dict[str, typing.Any]) -> list[dict]:
        async with self.request.app['db'].acquire() as conn:
            queryset = self.filter_queryset(self.get_queryset(), request_params)
            result = await conn.execute(queryset)
            flags = await result.fetchall()

        return [annotate_switch_with_expiration_date(switch=flag) for flag in flags]

    async def get_distinct_groups(self, request_params: dict[str, typing.Any]) -> list[str]:
        async with self.request.app['db'].acquire() as conn:
            queryset = self.filter_hidden(self.get_queryset(), request_params)
            result = await conn.execute(queryset)
            flags = await result.fetchall()
            return sorted({group for flag in flags for group in flag.groups})

    def get_queryset(self) -> Select:
        return switches.select()

    def order_queryset(self, qs: Select, request_params: dict[str, typing.Any]) -> Select:
        # Default ordering
        return qs.order_by(switches.c.created_at.desc())

    def filter_hidden(self, qs: Select, request_params: dict[str, typing.Any]) -> Select:
        if not request_params.get('show_hidden'):
            qs = qs.where(switches.c.deleted_at.is_(None))
        return qs

    def filter_group(self, qs: Select, request_params: dict[str, typing.Any]) -> Select:
        group = request_params.get('group')
        if group:
            qs = qs.where(switches.c.groups.any(group))
        return qs

    def filter_queryset(self, qs: Select, request_params: dict[str, typing.Any]) -> Select:
        qs = self.filter_hidden(qs, request_params)
        qs = self.filter_group(qs, request_params)
        return self.order_queryset(qs, request_params)


class SwitchDetailAdminView(web.View, UpdateMixin):
    validator = SwitchDetailAdminPostRequestSchema()
    permissions = [CanEditSwitch]
    model = switches

    async def get_context_data(
        self, switch: RowProxy | None = None, errors: ValidationError | None = None,
        updated: bool = False,
    ) -> dict[str, typing.Any]:
        switch = switch if switch else await self.get_object(self.request)
        switch_history = await get_switch_history(self.request, switch)

        svg_badge = get_switch_badge_svg(self.request.host, switch)
        markdown_badge = get_switch_markdown_badge(self.request, switch)

        context_data = {
            'object': switch,
            'svg_badge': svg_badge,
            'markdown_badge': markdown_badge,
            'switch_history': switch_history,
            'errors': errors,
            'updated': updated,
        }
        return context_data

    @aiohttp_jinja2.template('switches/detail.html')
    @login_required
    async def get(self) -> dict[str, typing.Any]:
        await self._check_permissions()

        switch_object = await self.get_object(self.request)

        if switch_object.deleted_at and switch_object.deleted_at <= utc_now():
            return {'object': None, 'errors': 'Oops! this switch was "deleted".'}

        return await self.get_context_data(switch=switch_object)

    @aiohttp_jinja2.template('switches/detail.html')
    @login_required
    async def post(self) -> dict[str, dict]:
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

    async def get_context_data(
        self, errors: ValidationError | None = None, user_input: dict | None = None,
    ) -> dict[str, typing.Any]:
        context_data = {
            'errors': errors,
            'ttl': settings.flag_ttl_days,
        }
        if user_input:
            context_data.update(user_input)
        return context_data

    async def resurrect_deleted_flag(self, form_data: MultiDictProxy) -> dict[str, typing.Any] | None:
        async with self.request.app['db'].acquire() as conn:
            result = await conn.execute(
                switches.select().where(switches.c.name == form_data['name']))
            already_created_switch = await result.first()

            if already_created_switch:
                try:
                    form_data = self._validate_form_data(form_data)  # type: ignore
                except ValidationError as error:
                    return await self.get_context_data(errors=error, user_input=dict(form_data))
                form_data['deleted_at'] = None  # type: ignore
                update_query = self.model.update().where(
                    self.model.c.id == str(already_created_switch.id),
                ).values(form_data)
                await conn.execute(update_query)

                new_value = str(form_data.get('is_active'))
                await save_switch_history(self.request, already_created_switch, new_value)

                location = self.request.app.router['switches_list'].url_for()
                raise web.HTTPFound(location=location)

    @aiohttp_jinja2.template('switches/add.html')
    @login_required
    async def get(self) -> dict[str, RowProxy]:
        return await self.get_context_data()

    @aiohttp_jinja2.template('switches/add.html')
    @login_required
    async def post(self) -> dict[str, dict]:
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
    remote_validator = RemoteSwitchesDataSchema()
    model = switches

    @staticmethod
    async def _get_switches_data() -> MultiDictProxy:
        async with ClientSession() as session:
            async with session.get(str(settings.sync_from_its_on_url)) as resp:
                resp.raise_for_status()
                return await resp.json()

    @aiohttp_jinja2.template('switches/error.html')
    @login_required
    async def post(self) -> dict[str, Exception]:
        update_existing = bool(self.request.rel_url.query.get('update_existing'))
        try:
            switches_data = await self._get_switches_data()
        except (ClientConnectionError, ClientResponseError) as error:
            return {'errors': error}
        try:
            switches_data = self.remote_validator.load(switches_data)
        except ValidationError as error:
            return {'errors': error}

        for switch_data in switches_data['result']:
            await self._create_or_update_switch(switch_data, update_existing)

        location = self.request.app.router['switches_list'].url_for()
        raise web.HTTPFound(location=location)

    async def _create_or_update_switch(
        self, switch_data: MultiDictProxy, update_existing: bool = False,
    ) -> None:
        try:
            await self.create_object(self.request, switch_data)
        except psycopg2.IntegrityError:
            if update_existing:
                await self._update_switch(switch_data)

    async def _update_switch(self, switch_data: MultiDictProxy) -> None:
        switch_data.pop('updated_at')  # type: ignore
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
            model_object = await self.get_object(self.request)
            update_query = self.model.update().where(self.model.c.id == object_pk).values(
                {'deleted_at': utc_now() + datetime.timedelta(days=model_object.ttl)})

            await conn.execute(update_query)
        location = self.request.app.router['switches_list'].url_for()
        raise web.HTTPFound(location=location)
