from __future__ import annotations
from typing import TYPE_CHECKING, Union

import aiohttp_jinja2
from aiohttp.abc import StreamResponse
from aiohttp.web import HTTPFound, View, Response
from aiohttp.web_exceptions import HTTPTemporaryRedirect
from aiohttp_security import forget, remember
from dynaconf import settings
from marshmallow.exceptions import ValidationError
from multidict import MultiDictProxy
from yarl import URL

from auth.auth import check_credentials, get_login_context
from auth.schemes import LoginPostRequestSchema

if TYPE_CHECKING:
    from typing import Optional, Dict


def redirect_uri(request):
    oauth_subbapp = request.app._subapps[0]
    url = str(request.url.with_path(str(oauth_subbapp.router["callback"].url_for())))
    if settings.OAUTH.force_https:
        return url.replace('http', 'https')
    return url


class OauthViewForceHttps(View):
    """Modified version of aiohttp_oauth2.client.views.AuthView to replace http by https"""

    async def get(self) -> Response:
        params = {
            "client_id": self.request.app["CLIENT_ID"],
            "redirect_uri": redirect_uri(self.request),
            "response_type": "code",
            **self.request.app["AUTH_EXTRAS"],
        }

        if self.request.app["SCOPES"]:
            params["scope"] = " ".join(self.request.app["SCOPES"])

        location = str(URL(self.request.app["AUTHORIZE_URL"]).with_query(params))

        return HTTPTemporaryRedirect(location=location)


class LoginView(View):
    @aiohttp_jinja2.template('users/login.html')
    async def get(self, error: Optional[str] = None) -> Dict[str, Union[str | bool]]:
        return await get_login_context()

    @aiohttp_jinja2.template('users/login.html')
    async def error(self) -> Dict[str, Union[str | bool]]:
        return await get_login_context('Authorization failed')

    @aiohttp_jinja2.template('users/login.html')
    async def only_oauth_error(self) -> Dict[str, Union[str | bool]]:
        return await get_login_context('Classic login is forbidden')

    async def authorise(
        self, response_location: Response, login: str, password: str,
    ) -> StreamResponse:
        if await check_credentials(self.request.app['db'], login, password):
            await remember(self.request, response_location, login)
            return response_location
        return await self.error()

    async def post(self) -> StreamResponse:
        only_oauth = getattr(getattr(settings, 'OAUTH', None), 'ONLY_OAUTH', False)
        if only_oauth:
            return await self.only_oauth_error()
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
