import datetime
import json
from typing import Any, Optional

import sqlalchemy as sa
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from aiohttp import web


def setup_cache(app: web.Application) -> None:
    cache = Cache.from_url(app['config']['cache_url'])
    cache.serializer = JsonSerializer()
    app['cache'] = cache


class AwareDateTime(sa.TypeDecorator):
    """Results returned as local datetimes with timezone."""

    impl = sa.DateTime

    def process_result_value(
        self, value: Optional[datetime.datetime], dialect: Any,
    ) -> Optional[datetime.datetime]:
        if not value:
            return None
        local_tzinfo = datetime.datetime.now().astimezone().tzinfo
        return value.replace(tzinfo=datetime.timezone.utc).astimezone(local_tzinfo)


class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime.datetime):
            return obj.astimezone(datetime.timezone.utc).isoformat()
        if isinstance(obj, (datetime.date, datetime.time)):
            return obj.isoformat()

        return super().default(obj)
