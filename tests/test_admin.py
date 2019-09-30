import pytest

from its_on.models import switches


async def test_switches_list_without_auhtorize(tables_and_data, client):
    response = await client.get('/zbs/switches')

    assert response.status == 401


async def test_update_switch_without_login(tables_and_data, client):
    response = await client.post('/zbs/switches/1', data={'version': 'some_shit'})

    assert response.status == 401


@pytest.mark.parametrize('switch_title, expected_result', [
    ('switch1', True),
    ('switch2', True),
    ('switch1488', False),
])
async def test_switches_list(tables_and_data, client, login, switch_title, expected_result):
    response = await client.get('/zbs/switches')

    content = await response.content.read()

    assert (switch_title in content.decode('utf-8')) is expected_result


async def test_switch_detail(tables_and_data, client, login, switch):
    response = await client.get('/zbs/switches/1')

    content = await response.content.read()

    assert switch.name in content.decode('utf-8')


async def test_switch_update(tables_and_data, client, login, switch):
    await client.post('/zbs/switches/1', data={'is_active': False})

    async with client.server.app['db'].acquire() as conn:
        result = await conn.execute(switches.select().where(switches.c.id == 1))
        updated_switch = await result.first()

    assert updated_switch.is_active is False
