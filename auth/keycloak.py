from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from keycloak import KeycloakOpenID

from its_on.config import settings

if TYPE_CHECKING:
    from aiohttp.web import Application, Request

logger = logging.getLogger(__name__)

DEVELOPER_ROLE = settings.OAUTH.DEVELOPER_ROLE
KEYCLOAK_TIMEOUT = 10


@lru_cache(maxsize=1)
def get_keycloak_openid() -> KeycloakOpenID:
    # Every KeycloakOpenID opens its own requests session and httpx client,
    # so the instance is shared instead of being built on each request.
    return KeycloakOpenID(
        server_url=settings.OAUTH.SERVER_URL,
        realm_name=settings.OAUTH.REALM_NAME,
        client_id=settings.OAUTH.CLIENT_ID,
        client_secret_key=settings.OAUTH.CLIENT_SECRET,
        timeout=KEYCLOAK_TIMEOUT,
    )


async def close_keycloak_openid(app: 'Application') -> None:
    if not get_keycloak_openid.cache_info().currsize:
        return

    await get_keycloak_openid().connection.aclose()
    get_keycloak_openid.cache_clear()


def build_callback_url(request: Request) -> str:
    url = str(request.url.with_path('/oauth/callback').with_query({}))
    if settings.OAUTH.FORCE_HTTPS:
        url = url.replace('http://', 'https://', 1)
    return url


def has_developer_role(decoded_token: dict) -> bool:
    resource_access = decoded_token.get('resource_access') or {}
    client_roles = resource_access.get(settings.OAUTH.CLIENT_ID, {}).get('roles', [])
    return DEVELOPER_ROLE in client_roles


def get_username_from_token(decoded_token: dict) -> str | None:
    return decoded_token.get('preferred_username')
