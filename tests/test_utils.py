import datetime

import pytest
from aiohttp.test_utils import make_mocked_request
from anybadge import Badge

from its_on.admin.utils import annotate_switch_with_expiration_date
from its_on.constants import (
    SVG_BADGE_BACKGROUND_COLOR,
    SWITCH_NOT_FOUND_SVG_BADGE_PREFIX,
    SWITCH_IS_INACTIVE_SVG_BADGE_PREFIX,
    SWITCH_IS_ACTIVE_SVG_BADGE_PREFIX,
    SWITCH_IS_HIDDEN_SVG_BADGE_PREFIX,
)
from its_on.utils import (
    get_switch_badge_prefix_and_value,
    get_switch_badge_svg,
    get_switch_markdown_badge,
)


@pytest.mark.freeze_time(datetime.datetime(2020, 5, 1, tzinfo=datetime.timezone.utc))
@pytest.mark.usefixtures('setup_tables_and_data')
@pytest.mark.parametrize(
    ('switch_params', 'expected_prefix', 'expected_value'),
    [
        (
            {
                'name': 'feature-flag-1',
                'is_active': True,
                'deleted_at': None,
            },
            SWITCH_IS_ACTIVE_SVG_BADGE_PREFIX,
            'feature-flag-1',
        ),
        (
            {
                'name': 'feature-flag-1',
                'is_active': False,
                'deleted_at': None,
            },
            SWITCH_IS_INACTIVE_SVG_BADGE_PREFIX,
            'feature-flag-1',
        ),
        (
            {
                'name': 'feature-flag-1',
                'deleted_at': datetime.datetime(2020, 5, 14, tzinfo=datetime.timezone.utc),
            },
            SWITCH_IS_HIDDEN_SVG_BADGE_PREFIX,
            'feature-flag-1 (hidden)',
        ),
        (
            {
                'name': 'feature-flag-1',
                'deleted_at': datetime.datetime(2020, 4, 1, tzinfo=datetime.timezone.utc),
            },
            SWITCH_IS_HIDDEN_SVG_BADGE_PREFIX,
            'feature-flag-1 (deleted)',
        ),
    ],
    ids=['active-flag', 'inactive-flag', 'hidden-flag', 'deleted-flag'],
)
async def test_get_switch_badge_prefix_and_value(
    switch_factory, switch_params, expected_prefix, expected_value,
):
    switch = await switch_factory(**switch_params)

    prefix, value = get_switch_badge_prefix_and_value(switch)

    assert prefix == expected_prefix
    assert value == expected_value


@pytest.mark.usefixtures('setup_tables_and_data', 'badge_mask_id_patch')
async def test_get_switch_badge_svg_for_active_switch(switch_factory):
    hostname = 'flags-staging.bestdoctor.ru'
    switch = await switch_factory(is_active=True, deleted_at=None)
    expected_badge = Badge(
        label=f'{SWITCH_IS_ACTIVE_SVG_BADGE_PREFIX} {hostname}', value=switch.name,
        default_color=SVG_BADGE_BACKGROUND_COLOR,
    )

    svg_badge = get_switch_badge_svg(hostname, switch)

    assert svg_badge == expected_badge.badge_svg_text


@pytest.mark.usefixtures('setup_tables_and_data', 'badge_mask_id_patch')
async def test_get_switch_badge_svg_for_inactive_switch(switch_factory):
    hostname = 'flags-staging.bestdoctor.ru'
    switch = await switch_factory(is_active=False, deleted_at=None)
    expected_badge = Badge(
        label=f'{SWITCH_IS_INACTIVE_SVG_BADGE_PREFIX} {hostname}', value=switch.name,
        default_color=SVG_BADGE_BACKGROUND_COLOR,
    )

    svg_badge = get_switch_badge_svg(hostname, switch)

    assert svg_badge == expected_badge.badge_svg_text


@pytest.mark.usefixtures('setup_tables_and_data', 'badge_mask_id_patch')
@pytest.mark.freeze_time(datetime.datetime(2020, 5, 1, tzinfo=datetime.timezone.utc))
async def test_get_switch_badge_svg_for_hidden_switch(switch_factory):
    hostname = 'flags-staging.bestdoctor.ru'
    switch = await switch_factory(
        deleted_at=datetime.datetime(2020, 5, 14, tzinfo=datetime.timezone.utc),
    )
    expected_badge = Badge(
        label=f'{SWITCH_IS_HIDDEN_SVG_BADGE_PREFIX} {hostname}',
        value=f'{switch.name} (hidden)',
        default_color=SVG_BADGE_BACKGROUND_COLOR,
    )

    svg_badge = get_switch_badge_svg(hostname, switch)

    assert svg_badge == expected_badge.badge_svg_text


@pytest.mark.usefixtures('setup_tables_and_data', 'badge_mask_id_patch')
@pytest.mark.freeze_time(datetime.datetime(2020, 5, 1, tzinfo=datetime.timezone.utc))
async def test_get_switch_badge_svg_for_deleted_switch(switch_factory):
    hostname = 'flags-staging.bestdoctor.ru'
    switch = await switch_factory(
        deleted_at=datetime.datetime(2020, 5, 1, tzinfo=datetime.timezone.utc),
    )
    expected_badge = Badge(
        label=f'{SWITCH_IS_HIDDEN_SVG_BADGE_PREFIX} {hostname}',
        value=f'{switch.name} (deleted)',
        default_color=SVG_BADGE_BACKGROUND_COLOR,
    )

    svg_badge = get_switch_badge_svg(hostname, switch)

    assert svg_badge == expected_badge.badge_svg_text


@pytest.mark.usefixtures('badge_mask_id_patch')
def test_get_switch_badge_svg_for_unknown_switch():
    hostname = 'flags-staging.bestdoctor.ru'
    expected_badge = Badge(
        label=f'{SWITCH_NOT_FOUND_SVG_BADGE_PREFIX} {hostname}',
        value='not found',
        default_color=SVG_BADGE_BACKGROUND_COLOR,
    )

    svg_badge = get_switch_badge_svg(hostname, switch=None)

    assert svg_badge == expected_badge.badge_svg_text


@pytest.mark.usefixtures('setup_tables_and_data', 'badge_mask_id_patch')
async def test_get_switch_markdown_badge(switch_factory, client):
    switch = await switch_factory()
    flag_url = str(client.make_url(f'/zbs/switches/{switch.id}'))
    svg_badge_url = str(client.make_url(f'/api/v1/switches/{switch.id}/svg-badge'))
    expected_badge = f'[![{switch.name}]({svg_badge_url})]({flag_url})'
    request = make_mocked_request(
        method='GET',
        path=svg_badge_url,
        app=client.app,
    )

    markdown_badge = get_switch_markdown_badge(request, switch)

    assert markdown_badge == expected_badge


@pytest.mark.parametrize(
    ('name', 'is_active', 'ttl', 'updated_at', 'expected_result'),
    [
        (
            'inactive_switch',
            False,
            14,
            datetime.datetime(2020, 5, 1),
            None,
        ),
        (
            'active_switch',
            True,
            14,
            datetime.datetime(2020, 5, 1),
            datetime.date(2020, 5, 15),
        ),
        (
            'other_active_switch',
            True,
            21,
            datetime.datetime(2020, 5, 5),
            datetime.date(2020, 5, 26),
        ),
    ],
)
@pytest.mark.usefixtures('setup_tables_and_data')
@pytest.mark.freeze_time(datetime.datetime(2020, 5, 1, tzinfo=datetime.timezone.utc))
async def test_annotate_flag_with_expiration_date(
    switch_factory, name, is_active, ttl, updated_at, expected_result,
):
    switch = await switch_factory(
        name=name,
        is_active=is_active,
        groups=('backend',),
        ttl=ttl,
        updated_at=updated_at,
        deleted_at=None,
    )

    result = annotate_switch_with_expiration_date(switch=switch)

    assert (result['expires_at'] and result['expires_at'].date()) == expected_result
