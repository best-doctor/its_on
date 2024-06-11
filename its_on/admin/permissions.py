import typing

from aiohttp import web
from aiohttp_security.api import check_authorized

from auth.utils import get_current_user, is_superuser
from its_on.admin.utils import get_user_switches
from its_on.models import switches


class BasePermission:
    @classmethod
    async def is_allowed(cls, request: web.Request, *args: typing.Any, **kwargs: typing.Any) -> bool:
        return await check_authorized(request) is not None


class CanEditSwitch(BasePermission):
    @classmethod
    async def is_allowed(cls, request: web.Request, object_to_check: switches) -> bool:
        if await is_superuser(request):
            return True

        user = await get_current_user(request)
        user_switches = await get_user_switches(request, user)

        return any(object_to_check.name == flag.name for flag in user_switches)


class CanEditUser(BasePermission):
    @classmethod
    async def is_allowed(cls, request: web.Request) -> bool:
        return await is_superuser(request)
