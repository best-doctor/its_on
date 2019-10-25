from typing import Optional, Dict

import aiohttp_jinja2
from aiohttp import web
from aiohttp_security import forget, remember
from marshmallow.exceptions import ValidationError
from multidict import MultiDictProxy

from .auth import check_credentials
from .schemes import LoginPostRequestSchema


class LoginView(web.View):
    @aiohttp_jinja2.template('users/login.html')
    async def get(self) -> Dict[str, str]:
        return {'context': ''}

    async def authorise(self, response_location: web.Response, login: str, password: str) -> web.Response:
        if await check_credentials(self.request.app['db'], login, password):
            await remember(self.request, response_location, login)
            return response_location

    async def post(self) -> web.Response:
        response_location = web.HTTPFound('/zbs/switches')
        form_data = await self.request.post()
        validated_data = self.validate_form_data(form_data)

        if not validated_data:
            return web.HTTPFound('/zbs')

        login, password = validated_data.get('login', ''), validated_data.get('password', '')

        return await self.authorise(response_location, login, password)

    def validate_form_data(self, form_data: MultiDictProxy) -> Optional[Dict[str, str]]:
        try:
            return LoginPostRequestSchema().load(form_data)
        except ValidationError:
            return None


class LogoutView(web.View):
    async def get(self) -> web.Response:
        response = web.HTTPFound('/zbs/login')

        await forget(self.request, response)
        return response
