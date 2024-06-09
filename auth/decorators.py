import typing

from aiohttp.web import Response, View
from aiohttp.web_exceptions import HTTPFound, HTTPUnauthorized
from aiohttp_security import check_authorized


def login_required(func: typing.Callable) -> typing.Callable:
    async def _login_required(self: View, *args: typing.Any, **kwargs: typing.Any) -> Response:
        try:
            await check_authorized(self.request)
        except HTTPUnauthorized:
            raise HTTPFound('/zbs/login')
        return await func(self, *args, **kwargs)
    return _login_required
