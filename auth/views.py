from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Union

import aiohttp_jinja2
from aiohttp.abc import StreamResponse
from aiohttp.web import HTTPFound, Response, View
from aiohttp.web_exceptions import HTTPTemporaryRedirect
from aiohttp_security import forget, remember
from aiohttp_jinja2 import render_template_async
from jwcrypto import jwt as jwcrypto_jwt
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakError
from marshmallow.exceptions import ValidationError
from multidict import MultiDictProxy

from auth.auth import check_credentials, get_login_context, get_or_create_user
from auth.keycloak import build_callback_url, get_keycloak_openid, get_username_from_token, has_developer_role
from auth.schemes import LoginPostRequestSchema
from its_on.app_keys import db_key
from its_on.config import settings

if TYPE_CHECKING:
    from typing import Optional, Dict

logger = logging.getLogger(__name__)


class OAuthCallbackError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class KeycloakLoginView(View):
    async def get(self) -> StreamResponse:
        keycloak_openid = get_keycloak_openid()
        callback_url = build_callback_url(self.request)
        auth_url = keycloak_openid.auth_url(redirect_uri=callback_url, scope='openid')
        raise HTTPTemporaryRedirect(location=auth_url)


class KeycloakCallbackView(View):

    @staticmethod
    async def _exchange_code_for_token(
        keycloak_openid: KeycloakOpenID,
        code: str,
        callback_url: str,
    ) -> dict:
        try:
            return await keycloak_openid.a_token(
                grant_type='authorization_code',
                code=code,
                redirect_uri=callback_url,
            )
        except (KeycloakError, TypeError):
            logger.exception('Keycloak token exchange failed')
            raise OAuthCallbackError('Keycloak authentication failed')

    @staticmethod
    async def _decode_access_token(
        keycloak_openid: KeycloakOpenID,
        access_token: str,
    ) -> dict:
        try:
            return await keycloak_openid.a_decode_token(
                access_token,
                validate=True,
            )
        except (KeycloakError, jwcrypto_jwt.JWException):
            logger.exception('Token decode failed')
            raise OAuthCallbackError('Token validation failed')

    async def get(self) -> StreamResponse:
        code = self.request.query.get('code')
        if not code:
            return await self._render_login_error('Missing authorization code')

        keycloak_openid = get_keycloak_openid()
        callback_url = build_callback_url(self.request)

        try:
            token = await self._exchange_code_for_token(keycloak_openid, code, callback_url)
            decoded = await self._decode_access_token(keycloak_openid, token['access_token'])
        except OAuthCallbackError as err:
            return await self._render_login_error(err.message)

        if not has_developer_role(decoded):
            return await self._render_login_error('Access denied: developers role required')

        username = get_username_from_token(decoded)
        if not username:
            return await self._render_login_error('Could not determine username from token')

        await get_or_create_user(self.request.app[db_key], username)

        response = HTTPFound('/zbs/switches')
        await remember(self.request, response, username)
        raise response

    async def _render_login_error(self, error: str) -> StreamResponse:
        context = await get_login_context(error=error)
        return await render_template_async('users/login.html', self.request, context)


class LoginView(View):
    async def get(self) -> StreamResponse:
        if getattr(getattr(settings, 'OAUTH', None), 'IS_ENABLED', False):
            raise HTTPFound('/oauth/auth')
        context = await get_login_context()
        return await render_template_async('users/login.html', self.request, context)

    @aiohttp_jinja2.template('users/login.html')
    async def error(self) -> Dict[str, Union[str | bool]]:
        return await get_login_context('Authorization failed')

    @aiohttp_jinja2.template('users/login.html')
    async def only_oauth_error(self) -> Dict[str, Union[str | bool]]:
        return await get_login_context('Classic login is forbidden')

    async def authorise(
        self, response_location: HTTPFound, login: str, password: str,
    ) -> StreamResponse:
        if await check_credentials(self.request.app[db_key], login, password):
            await remember(self.request, response_location, login)
            raise response_location
        return await self.error()

    async def post(self) -> StreamResponse:
        is_oauth_enabled = getattr(getattr(settings, 'OAUTH', None), 'IS_ENABLED', False)
        if is_oauth_enabled:
            return await self.only_oauth_error()
        response_location = HTTPFound('/zbs/switches')
        form_data = await self.request.post()
        validated_data = self.validate_form_data(form_data)

        if not validated_data:
            raise HTTPFound('/zbs')

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
        raise response
