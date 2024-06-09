from aiocache import Cache
from aiocache.serializers import JsonSerializer
from aiohttp import web
from typing import Callable


def setup_cache(app: web.Application) -> None:
    cache_url = str(app['config'].cache_url)
    cache = Cache.from_url(cache_url)
    cache.serializer = JsonSerializer()
    app['cache'] = cache


def switch_list_cache_key_builder(method: Callable, view: web.View) -> str:
    validated_data = view.request['validated_data']
    group_name = validated_data['group']
    is_active = validated_data.get('is_active')
    version = validated_data.get('version')
    return f'switch_list__{group_name}__{version}__{is_active}'
