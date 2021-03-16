import datetime
import json
from typing import Any

from aiocache import Cache
from aiocache.serializers import JsonSerializer
from aiohttp import web


def setup_cache(app: web.Application) -> None:
    cache = Cache.from_url(app['config']['cache_url'])
    cache.serializer = JsonSerializer()
    app['cache'] = cache


class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj) -> Any:
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()

        return super().default(obj)
