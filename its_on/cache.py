from urllib.parse import urlparse

from aiocache import Cache
from aiocache.serializers import JsonSerializer
from aiohttp import web
from typing import Callable

from its_on.app_keys import cache_key, config_key


def setup_cache(app: web.Application) -> None:
    parsed = urlparse(app[config_key]['cache_url'])
    cache = Cache(
        Cache.REDIS,
        endpoint=parsed.hostname or 'localhost',
        port=parsed.port or 6379,
        db=int(parsed.path.lstrip('/') or 0),
    )
    cache.serializer = JsonSerializer()
    app[cache_key] = cache


def switch_list_cache_key_builder(method: Callable, view: web.View) -> str:
    validated_data = view.request['validated_data']
    group_name = validated_data['group']
    is_active = validated_data.get('is_active')
    version = validated_data.get('version')
    return f'switch_list__{group_name}__{version}__{is_active}'
