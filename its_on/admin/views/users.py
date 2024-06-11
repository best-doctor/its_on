import typing

import aiohttp_jinja2
from aiohttp import web
from aiopg.sa.result import RowProxy
from marshmallow.exceptions import ValidationError
from multidict import MultiDictProxy, MultiDict
from sqlalchemy.sql import Select

from auth.decorators import login_required
from auth.models import users
from its_on.admin.mixins import UpdateMixin
from its_on.admin.permissions import CanEditUser
from its_on.admin.schemes import UserDetailPostRequestSchema
from its_on.admin.utils import get_user_switches_names
from its_on.admin.views.query_utils import (
    create_new_user_switch,
    is_user_switch_exist,
    remove_user_switches,
)
from its_on.models import switches
from its_on.utils import utc_now


class UserListAdminView(web.View):
    model = switches

    @aiohttp_jinja2.template('users/list.html')
    @login_required
    async def get(self) -> dict[str, list[RowProxy] | None]:
        users = await self.get_response_data()
        return {'users': users}

    async def get_response_data(self) -> list[RowProxy]:
        objects = await self.load_objects()
        return objects

    async def load_objects(self) -> list:
        async with self.request.app['db'].acquire() as conn:
            queryset = self.get_queryset()
            result = await conn.execute(queryset)
            return await result.fetchall()

    def get_queryset(self) -> Select:
        return users.select()


class UserDetailAdminView(web.View, UpdateMixin):
    validator = UserDetailPostRequestSchema()
    permissions = [CanEditUser]
    model = users

    async def get_context_data(
        self,
        errors: ValidationError | None = None,
        updated: bool = False,
        switches: list | None = None,
        user_switches: list | None = None,
    ) -> dict[str, typing.Any]:

        user_object = await self.get_object(self.request)
        switches = switches if switches else await self.get_switches()
        user_switches = user_switches if user_switches else await get_user_switches_names(self.request, user_object)

        context_data = {
            'object': user_object,
            'errors': errors,
            'updated': updated,
            'switches': switches,
            'user_switches': user_switches,
        }
        return context_data

    async def get_switches(self) -> RowProxy:
        async with self.request.app['db'].acquire() as conn:
            queryset = switches.select(
                whereclause=(switches.c.deleted_at.is_(None) | (switches.c.deleted_at > utc_now())),
            )
            result = await conn.execute(queryset)
            return await result.fetchall()

    @aiohttp_jinja2.template('users/detail.html')
    @login_required
    async def get(self) -> dict[str, RowProxy]:
        await self._check_permissions()

        return await self.get_context_data()

    @aiohttp_jinja2.template('users/detail.html')
    @login_required
    async def post(self) -> dict[str, dict]:
        await self._check_permissions()

        form_data = await self.request.post()
        await self._handle_user_switches(form_data)
        to_update = self._get_to_update(form_data)

        try:
            await self.update_object(self.request, to_update)
        except ValidationError as error:
            return await self.get_context_data(errors=error)

        return await self.get_context_data(updated=True)

    def _get_to_update(self, form_data: MultiDictProxy) -> MultiDict | MultiDictProxy:
        """
        Удаляет поля switch_ids, которых нет в модели users.

        aiohttp возвращает post данные в MultiDictProxy, который неизменяем, приходится делать копию
        """
        if not form_data.get('switch_ids'):
            return form_data

        to_update = form_data.copy()
        to_update.popall('switch_ids')
        return to_update

    def _get_user_switches_ids_to_update(self, form_data: MultiDictProxy) -> list[str | None]:
        switches_ids: list

        if form_data.get('switch_ids') is None:
            switches_ids = []
        else:
            switches_ids = form_data.getall('switch_ids')

        return switches_ids

    async def _handle_user_switches(self, form_data: MultiDictProxy) -> None:
        user_object = await self.get_object(self.request)

        switches_ids = self._get_user_switches_ids_to_update(form_data)

        await remove_user_switches(self.request, user_object, switches_ids)

        if not switches_ids:
            return None

        for switch_id in switches_ids:
            if not await is_user_switch_exist(self.request, switch_id, user_object.id):
                await create_new_user_switch(self.request, switch_id, user_object.id)

    async def _check_permissions(self) -> None:
        for permission in self.permissions:
            if not await permission.is_allowed(self.request):
                raise web.HTTPForbidden
