import datetime

import pytest

from its_on.utils import get_switch_badge_svg


async def test_switch(setup_tables_and_data, client):
    response = await client.get('/api/v1/switch?group=group1')

    assert response.status == 200
    assert await response.json() == {'count': 3, 'result': ['switch1', 'switch2', 'switch4']}


@pytest.mark.parametrize(
    'value', ['1', 'on', 'true', 'yes'],
)
async def test_switch_active(setup_tables_and_data, client, value):
    response = await client.get(f'/api/v1/switch?group=group1&is_active={value}')

    assert response.status == 200
    assert await response.json() == {'count': 3, 'result': ['switch1', 'switch2', 'switch4']}


@pytest.mark.parametrize(
    'value', ['0', 'off', 'false', 'no'],
)
async def test_switch_inactive(setup_tables_and_data, client, value):
    response = await client.get(f'/api/v1/switch?group=group1&is_active={value}')

    assert response.status == 200
    assert await response.json() == {'count': 1, 'result': ['switch3']}


async def test_switch_without_params(setup_tables_and_data, client):
    response = await client.get('/api/v1/switch')

    assert response.status == 422
    assert await response.json() == {'group': ['Missing data for required field.']}


@pytest.mark.parametrize('group,expected_result', [
    ('group1', {'count': 3, 'result': ['switch1', 'switch2', 'switch4']}),
    ('group2', {'count': 2, 'result': ['switch1', 'switch5']}),
])
async def test_switch_filter_by_group(group, expected_result, setup_tables_and_data, client):
    response = await client.get(f'/api/v1/switch?group={group}')

    assert response.status == 200
    assert await response.json() == expected_result


async def test_switch_cors(client):
    response = await client.get(
        '/api/v1/switch?group=group1',
        headers={'Origin': 'http://localhost:8081'},
    )

    assert response.status == 200
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:8081'


async def test_switch_cors_options(client):
    response = await client.options('/api/v1/switch', headers={
        'Origin': 'http://localhost:8081',
        'Access-Control-Request-Method': 'GET',
    })

    assert response.status == 200
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:8081'


@pytest.mark.parametrize('version,expected_result', [
    (1, {'count': 0, 'result': []}),
    (4, {'count': 1, 'result': ['switch4']}),
    (100, {'count': 1, 'result': ['switch4']}),
])
async def test_switch_filter_by_version(version, expected_result, setup_tables_and_data, client):
    response = await client.get(f'/api/v1/switch?group=group1&version={version}')

    assert response.status == 200
    assert await response.json() == expected_result


async def test_switches_full_info(
    switches_factory, client, asserted_switch_full_info_data,
):
    all_switches = await switches_factory(batch_size=5)
    response = await client.get('/api/v1/switches_full_info')

    assert response.status == 200
    assert await response.json() == asserted_switch_full_info_data(all_switches)


@pytest.mark.freeze_time(datetime.datetime(2020, 5, 1, tzinfo=datetime.timezone.utc))
async def test_switches_deleted_at(
    switch_factory, client, asserted_switch_full_info_data,
):
    expected_flags = [
        await switch_factory(
            name='switch1',
            is_active=True,
            groups=('backend',),
            deleted_at=None,
        ),
        await switch_factory(
            name='switch2',
            is_active=True,
            groups=('backend',),
            deleted_at=datetime.datetime(2020, 5, 1, 1, tzinfo=datetime.timezone.utc),
        ),
    ]
    await switch_factory(
        name='switch3',
        is_active=True,
        groups=('backend',),
        deleted_at=datetime.datetime(2020, 4, 1, tzinfo=datetime.timezone.utc),
    )
    await switch_factory(
        name='switch4',
        is_active=True,
        groups=('backend',),
        deleted_at=datetime.datetime(2020, 5, 1, tzinfo=datetime.timezone.utc),
    )
    expected_flag_names = [flag['name'] for flag in expected_flags]

    response = await client.get('/api/v1/switch?group=backend')

    assert response.status == 200
    assert await response.json() == {
        'count': len(expected_flag_names), 'result': expected_flag_names,
    }


@pytest.mark.usefixtures('badge_mask_id_patch')
async def test_switch_svg_badge_view(
    switch_factory, client, asserted_switch_full_info_data,
):
    switch = await switch_factory()
    expected_badge_svg = get_switch_badge_svg(
        hostname=f'{client.host}:{client.port}',
        switch=switch,
    )

    response = await client.get(f'/api/v1/switches/{switch.id}/svg-badge')

    assert response.status == 200
    assert await response.text() == expected_badge_svg
