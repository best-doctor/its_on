from aiocache import Cache
from aiocache.serializers import JsonSerializer
from aiohttp import web


def setup_cache(app: web.Application) -> None:
    cache = Cache.from_url(app['config']['cache_url'])
    cache.serializer = JsonSerializer()
    app['cache'] = cache
