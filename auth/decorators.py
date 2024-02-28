from typing import Callable, Any

from aiohttp.web import Response, View
from aiohttp.web_exceptions import HTTPFound, HTTPUnauthorized
from aiohttp_security import check_authorized


def login_required(func: Callable) -> Callable:
    async def _login_required(self: View, *args: Any, **kwargs: Any) -> Response:
        try:
            await check_authorized(self.request)
        except HTTPUnauthorized:
            raise HTTPFound('/zbs/login')
        return await func(self, *args, **kwargs)
    return _login_required
