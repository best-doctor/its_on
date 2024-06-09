from __future__ import annotations

import datetime
import json
import typing

import sqlalchemy as sa
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from aiohttp import web
from aiopg.sa.result import RowProxy
from anybadge import Badge

from its_on.constants import (
    SVG_BADGE_BACKGROUND_COLOR,
    SWITCH_IS_HIDDEN_SVG_BADGE_PREFIX,
    SWITCH_IS_ACTIVE_SVG_BADGE_PREFIX,
    SWITCH_IS_INACTIVE_SVG_BADGE_PREFIX,
    SWITCH_NOT_FOUND_SVG_BADGE_PREFIX,
)


def setup_cache(app: web.Application) -> None:
    cache = Cache.from_url(app['config']['cache_url'])
    cache.serializer = JsonSerializer()
    app['cache'] = cache


def reverse(
    request: web.Request,
    router_name: str,
    params: dict[str, str] | None = None,
    with_query: dict[str, typing.Any] | None = None,
) -> str:
    if not params:
        params = {}
    path_url = request.app.router[router_name].url_for(**params).with_query(with_query)
    return str(request.url.join(path_url))


def get_switch_badge_prefix_and_value(switch: RowProxy) -> tuple[str, str]:
    value = switch.name
    if switch.deleted_at and switch.deleted_at <= utc_now():
        prefix = SWITCH_IS_HIDDEN_SVG_BADGE_PREFIX
        value = value + ' (deleted)'
    elif switch.deleted_at:
        prefix = SWITCH_IS_HIDDEN_SVG_BADGE_PREFIX
        value = value + ' (hidden)'
    elif switch.is_active:
        prefix = SWITCH_IS_ACTIVE_SVG_BADGE_PREFIX
    else:
        prefix = SWITCH_IS_INACTIVE_SVG_BADGE_PREFIX

    return prefix, value


def get_switch_badge_svg(hostname: str, switch: RowProxy | None = None) -> str:
    if switch is not None:
        prefix, value = get_switch_badge_prefix_and_value(switch)
    else:
        prefix = SWITCH_NOT_FOUND_SVG_BADGE_PREFIX
        value = 'not found'

    badge = Badge(
        label=f'{prefix} {hostname}', value=value,
        default_color=SVG_BADGE_BACKGROUND_COLOR,
    )

    return badge.badge_svg_text


def get_switch_markdown_badge(request: web.Request, switch: RowProxy) -> str:
    flag_url = reverse(request=request, router_name='switch_detail', params={'id': str(switch.id)})
    svg_badge_url = reverse(
        request=request, router_name='switch_svg_badge', params={'id': str(switch.id)},
    )

    return f'[![{switch.name}]({svg_badge_url})]({flag_url})'


class AwareDateTime(sa.TypeDecorator):
    """Results returned as local datetimes with timezone."""

    impl = sa.DateTime

    def process_result_value(
        self, value: datetime.datetime | None, dialect: typing.Any,
    ) -> datetime.datetime | None:
        if not value:
            return None
        return localize_datetime(value)


class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj: typing.Any) -> typing.Any:
        if isinstance(obj, datetime.datetime):
            return obj.astimezone(datetime.timezone.utc).isoformat()
        if isinstance(obj, (datetime.date, datetime.time)):
            return obj.isoformat()

        return super().default(obj)


def utc_now() -> datetime.datetime:
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


def localize_datetime(dt: datetime.datetime) -> datetime.datetime:
    return dt.replace(tzinfo=datetime.timezone.utc).astimezone(local_timezone())


def local_timezone() -> datetime.tzinfo | None:
    return datetime.datetime.now().astimezone().tzinfo
