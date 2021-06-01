import datetime

import pytest
from freezegun import freeze_time

from auth.models import users
from its_on.models import switch_history, switches


async def test_switches_list_without_auhtorize(setup_tables_and_data, client):
    response = await client.get('/zbs/switches')

    assert response.status == 401


async def test_update_switch_without_login(setup_tables_and_data, client):
    response = await client.post('/zbs/switches/1', data={'version': 'some_shit'})

    assert response.status == 401


@pytest.mark.parametrize('switch_title, expected_result', [
    ('switch1', True),
    ('switch2', True),
    ('switch1488', False),
])
async def test_switches_list(setup_tables_and_data, client, login, switch_title, expected_result):
    response = await client.get('/zbs/switches')

    content = await response.content.read()

    assert (switch_title in content.decode('utf-8')) is expected_result


async def test_switch_detail(setup_tables_and_data, client, login, switch):
    response = await client.get('/zbs/switches/1')

    content = await response.content.read()

    assert switch.name in content.decode('utf-8')


@freeze_time(datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc))
async def test_switch_add(setup_tables_and_data, client, login, switch):
    response = await client.get('/zbs/switches/add')
    content = await response.content.read()

    assert 'Flag adding' in content.decode('utf-8')

    switch_data = {
        'name': 'switch_to_check_add',
        'is_active': True,
        'groups': 'check_adding, group2,    ,,',
        'version': 1,
        'comment': 'This is the story of a big bad wolf an little girl whose name was Little Red Riding Hood',
    }
    response = await client.post('/zbs/switches/add', data=switch_data)
    content = await response.content.read()

    assert 'Switches list' in content.decode('utf-8')

    switch_data['is_hidden'] = False

    async with client.server.app['db'].acquire() as conn:
        result = await conn.execute(switches.select().where(switches.c.name == switch_data['name']))
        created_switch = await result.first()

    for field_name, field_value in switch_data.items():
        if field_name == 'groups':
            field_value = list(
                filter(None, [item.strip() for item in field_value.split(',')]),
            )
        assert getattr(created_switch, field_name) == field_value

    assert created_switch.created_at == datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc)


async def test_switch_update(setup_tables_and_data, client, login, switch):
    with freeze_time('2020-08-15'):
        await client.post('/zbs/switches/1', data={'is_active': False, 'groups': 'group1, group2'})

    async with client.server.app['db'].acquire() as conn:
        switches_query_result = await conn.execute(switches.select().where(switches.c.id == 1))
        updated_switch = await switches_query_result.first()
        switch_history_query_result = await conn.execute(
            switch_history.select().where(switch_history.c.switch_id == updated_switch.id),
        )
        new_switch_history = await switch_history_query_result.first()
        admin_query_result = await conn.execute(users.select().where(users.c.login == 'admin'))
        admin = await admin_query_result.first()

    assert updated_switch.is_active is False
    assert updated_switch.created_at == datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc)
    assert updated_switch.updated_at == datetime.datetime(2020, 8, 15, tzinfo=datetime.timezone.utc)
    assert new_switch_history is not None
    assert new_switch_history.new_value == 'False'
    assert new_switch_history.user_id == admin.id
    assert new_switch_history.changed_at == datetime.datetime(
        2020, 8, 15, tzinfo=datetime.timezone.utc,
    )


async def test_switch_soft_delete(setup_tables_and_data, client, login, switch):
    response = await client.get('/zbs/switches')
    content = await response.content.read()

    assert 'switch7' in content.decode('utf-8')

    await client.get('/zbs/switches/7/delete')

    response = await client.get('/zbs/switches')
    content = await response.content.read()

    assert 'switch7' not in content.decode('utf-8')


async def test_resurrect_switch(setup_tables_and_data, client, login, switch):
    response = await client.get('/zbs/switches')
    content = await response.content.read()

    assert 'switch3' in content.decode('utf-8')

    await client.get('/zbs/switches/3/delete')

    response = await client.get('/zbs/switches')
    content = await response.content.read()

    assert 'switch3' not in content.decode('utf-8')

    switch_data = {
        'name': 'switch3',
        'is_active': False,
        'is_hidden': False,
        'groups': 'group1',
        'version': 4,
    }
    response = await client.post('/zbs/switches/add', data=switch_data)
    content = await response.content.read()

    assert 'switch3' in content.decode('utf-8')


async def test_switches_copy_without_auhtorize(setup_tables_and_data, client):
    response = await client.post('/zbs/switches/copy')

    assert response.status == 401


@pytest.mark.parametrize(
    ('http_get_arguments', 'old_switch_is_active_expected', 'expected_updated_at'), [
        ('', True, datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc)),
        ('?update_existing=true', False, datetime.datetime(2020, 10, 15, tzinfo=datetime.timezone.utc)),
    ],
)
@freeze_time(datetime.datetime(2020, 10, 15, tzinfo=datetime.timezone.utc))
@pytest.mark.usefixtures('setup_tables_and_data', 'get_switches_data_mocked_existing_switch')
async def test_switches_copy_existing_switch_foo(
    client, login,
    http_get_arguments, old_switch_is_active_expected, expected_updated_at,
):
    response = await client.post(f'/zbs/switches/copy{http_get_arguments}')
    async with client.server.app['db'].acquire() as conn:
        result = await conn.execute(switches.count())
        switches_count = await result.first()
        switches_count = switches_count[0]

        result = await conn.execute(switches.select().where(switches.c.name == 'switch7'))
        old_switch = await result.first()

    assert response.status == 200
    assert switches_count == 7
    assert old_switch.is_active == old_switch_is_active_expected
    assert old_switch.updated_at == expected_updated_at


@pytest.mark.usefixtures('setup_tables_and_data', 'get_switches_data_mocked_new_switch')
async def test_switches_copy_new_switch(client, login):
    response = await client.post('/zbs/switches/copy')
    async with client.server.app['db'].acquire() as conn:
        result = await conn.execute(
            switches.select().where(switches.c.name == 'extremely_new_switch'))
        new_switch = await result.first()

    assert response.status == 200
    assert new_switch is not None
    assert new_switch.name == 'extremely_new_switch'
