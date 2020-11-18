import pytest


async def test_switch(setup_tables_and_data, client):
    response = await client.get('/api/v1/switch?group=group1')

    assert response.status == 200
    assert await response.json() == {'count': 3, 'result': ['switch1', 'switch2', 'switch4']}


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
    response = await client.get(f'/api/v1/switch?group=group1', headers={'Origin': 'http://localhost:8081'})

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
    setup_tables_and_data, client, switches_full_info_expected_result,
):
    response = await client.get(f'/api/v1/switches_full_info')

    assert response.status == 200
    assert await response.json() == switches_full_info_expected_result
