from typing import Any, Dict, List, Optional

import aiohttp_jinja2
import psycopg2
import sqlalchemy as sa
from aiohttp import web
from aiopg.sa.result import RowProxy
from marshmallow.exceptions import ValidationError
from multidict import MultiDictProxy
from sqlalchemy.sql import Select

from auth.decorators import login_required
from its_on.admin.mixins import CreateMixin
from its_on.admin.permissions import CanEditEnvironment
from its_on.admin.schemes import EnvironmentAddAdminPostRequestSchema
from its_on.app_keys import db_key
from its_on.models import environments, switch_environments


class EnvironmentBaseAdminView(web.View):
    """Справочник окружений глобальный, поэтому доступен только суперюзерам."""

    permissions = [CanEditEnvironment]

    async def _check_permissions(self) -> None:
        for permission in self.permissions:
            if not await permission.is_allowed(self.request):
                raise web.HTTPForbidden


class EnvironmentListAdminView(EnvironmentBaseAdminView):
    @aiohttp_jinja2.template('environments/list.html')
    @login_required
    async def get(self) -> Dict[str, List[RowProxy]]:
        await self._check_permissions()

        return {'environments': await self.load_objects()}

    async def load_objects(self) -> List[RowProxy]:
        async with self.request.app[db_key].acquire() as conn:
            result = await conn.execute(self.get_queryset())
            return await result.fetchall()

    def get_queryset(self) -> Select:
        return (
            sa.select([
                environments,
                sa.func.count(switch_environments.c.id).label('switches_count'),
            ])
            .select_from(
                environments.outerjoin(
                    switch_environments, switch_environments.c.environment_id == environments.c.id,
                ),
            )
            .group_by(environments.c.id)
            .order_by(environments.c.name)
        )


class EnvironmentAddAdminView(EnvironmentBaseAdminView, CreateMixin):
    validator = EnvironmentAddAdminPostRequestSchema()
    model = environments

    def get_context_data(
        self, errors: Optional[Exception] = None, user_input: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        context_data: Dict[str, Any] = {'errors': errors}
        if user_input:
            context_data.update(user_input)
        return context_data

    @aiohttp_jinja2.template('environments/add.html')
    @login_required
    async def get(self) -> Dict[str, Any]:
        await self._check_permissions()

        return self.get_context_data()

    @aiohttp_jinja2.template('environments/add.html')
    @login_required
    async def post(self) -> Dict[str, Any]:
        await self._check_permissions()

        form_data: MultiDictProxy = await self.request.post()
        try:
            await self.create_object(self.request, form_data)
        except (ValidationError, psycopg2.IntegrityError) as error:
            return self.get_context_data(errors=error, user_input=dict(form_data))

        location = self.request.app.router['environments_list'].url_for()
        raise web.HTTPFound(location=location)


class EnvironmentDeleteAdminView(EnvironmentBaseAdminView):
    @login_required
    async def post(self) -> None:
        """Удаляет окружение целиком, записи switch_environments удаляются каскадом."""
        await self._check_permissions()

        async with self.request.app[db_key].acquire() as conn:
            await conn.execute(
                environments.delete().where(environments.c.id == self.request.match_info['id']),
            )

        location = self.request.app.router['environments_list'].url_for()
        raise web.HTTPFound(location=location)
