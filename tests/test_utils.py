import pytest
from aiohttp.test_utils import make_mocked_request
from anybadge import Badge

from its_on.constants import (
    SVG_BADGE_BACKGROUND_COLOR,
    SWITCH_NOT_FOUND_SVG_BADGE_PREFIX,
    SWITCH_IS_INACTIVE_SVG_BADGE_PREFIX,
    SWITCH_IS_ACTIVE_SVG_BADGE_PREFIX,
    SWITCH_IS_HIDDEN_SVG_BADGE_PREFIX,
)
from its_on.utils import get_switch_badge_svg, get_switch_markdown_badge


@pytest.mark.usefixtures('setup_tables_and_data', 'badge_mask_id_patch')
async def test_get_switch_badge_svg_for_active_switch(switch_factory):
    hostname = 'flags-staging.bestdoctor.ru'
    switch = await switch_factory(is_active=True, is_hidden=False)
    expected_badge = Badge(
        label=f'{SWITCH_IS_ACTIVE_SVG_BADGE_PREFIX} {hostname}', value=switch.name,
        default_color=SVG_BADGE_BACKGROUND_COLOR,
    )

    svg_badge = get_switch_badge_svg(hostname, switch)

    assert svg_badge == expected_badge.badge_svg_text


@pytest.mark.usefixtures('setup_tables_and_data', 'badge_mask_id_patch')
async def test_get_switch_badge_svg_for_inactive_switch(switch_factory):
    hostname = 'flags-staging.bestdoctor.ru'
    switch = await switch_factory(is_active=False, is_hidden=False)
    expected_badge = Badge(
        label=f'{SWITCH_IS_INACTIVE_SVG_BADGE_PREFIX} {hostname}', value=switch.name,
        default_color=SVG_BADGE_BACKGROUND_COLOR,
    )

    svg_badge = get_switch_badge_svg(hostname, switch)

    assert svg_badge == expected_badge.badge_svg_text


@pytest.mark.usefixtures('setup_tables_and_data', 'badge_mask_id_patch')
async def test_get_switch_badge_svg_for_deleted_switch(switch_factory):
    hostname = 'flags-staging.bestdoctor.ru'
    switch = await switch_factory(is_hidden=True)
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
