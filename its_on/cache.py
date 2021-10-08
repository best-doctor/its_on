from aiocache import Cache
from aiocache.serializers import JsonSerializer
from aiohttp import web
from typing import Callable


def setup_cache(app: web.Application) -> None:
    cache = Cache.from_url(app['config']['cache_url'])
    cache.serializer = JsonSerializer()
    app['cache'] = cache


def switch_list_cache_key_builder(method: Callable, view: web.View) -> str:
    validated_data = view.request['validated_data']
    group_name = validated_data['group']
    version = validated_data.get('version')
    return f'switch_list__{view.__class__}__{group_name}__{version}'
