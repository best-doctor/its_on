import pytest


async def test_switch(tables_and_data, client):
    response = await client.get('/api/v1/switch?group=group1')

    assert response.status == 200
    assert await response.json() == {'count': 3, 'result': ['switch1', 'switch2', 'switch4']}


async def test_switch_without_params(tables_and_data, client):
    response = await client.get('/api/v1/switch')

    assert response.status == 422
    assert await response.json() == {'group': ['Missing data for required field.']}


@pytest.mark.parametrize('group,expected_result', [
    ('group1', {'count': 3, 'result': ['switch1', 'switch2', 'switch4']}),
    ('group2', {'count': 1, 'result': ['switch5']}),
])
async def test_switch_filter_by_group(group, expected_result, tables_and_data, client):
    response = await client.get(f'/api/v1/switch?group={group}')

    assert response.status == 200
    assert await response.json() == expected_result


@pytest.mark.parametrize('version,expected_result', [
    (1, {'count': 0, 'result': []}),
    (4, {'count': 1, 'result': ['switch4']}),
    (100, {'count': 1, 'result': ['switch4']}),
])
async def test_switch_filter_by_version(version, expected_result, tables_and_data, client):
    response = await client.get(f'/api/v1/switch?group=group1&version={version}')

    assert response.status == 200
    assert await response.json() == expected_result