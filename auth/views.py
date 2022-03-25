from __future__ import annotations
from typing import TYPE_CHECKING

import aiohttp_jinja2
from aiohttp.abc import StreamResponse
from aiohttp.web import HTTPFound, View, Response
from aiohttp_security import forget, remember
from marshmallow.exceptions import ValidationError
from multidict import MultiDictProxy

from auth.auth import check_credentials
from auth.schemes import LoginPostRequestSchema

if TYPE_CHECKING:
    from typing import Optional, Dict


class LoginView(View):
    @aiohttp_jinja2.template('users/login.html')
    async def get(self, error: Optional[str] = None) -> Dict[str, str]:
        return {'context': ''}

    @aiohttp_jinja2.template('users/login.html')
    async def error(self) -> Dict[str, str]:
        return {'context': '', 'error': 'Authorization failed'}

    async def authorise(
        self, response_location: Response, login: str, password: str
    ) -> StreamResponse:
        if await check_credentials(self.request.app['db'], login, password):
            await remember(self.request, response_location, login)
            return response_location
        return await self.error()

    async def post(self) -> StreamResponse:
        response_location = HTTPFound('/zbs/switches')
        form_data = await self.request.post()
        validated_data = self.validate_form_data(form_data)

        if not validated_data:
            return HTTPFound('/zbs')

        login, password = validated_data.get('login', ''), validated_data.get('password', '')

        return await self.authorise(response_location, login, password)

    def validate_form_data(self, form_data: MultiDictProxy) -> Optional[Dict[str, str]]:
        try:
            return LoginPostRequestSchema().load(form_data)
        except ValidationError:
            return None


class LogoutView(View):
    async def get(self) -> Response:
        response = HTTPFound('/zbs/login')

        await forget(self.request, response)
        return response
