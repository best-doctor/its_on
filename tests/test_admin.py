import datetime

import pytest
from aiohttp.test_utils import make_mocked_request
from aiohttp.web_exceptions import HTTPOk
from freezegun import freeze_time
from sqlalchemy import desc

from auth.models import users
from its_on.models import switch_history, switches
from its_on.settings import settings
from its_on.utils import get_switch_badge_svg, get_switch_markdown_badge, local_timezone, utc_now


@pytest.mark.usefixtures('setup_tables_and_data')
async def test_switches_list_without_authorization(client, login_path):
    response = await client.get('/zbs/switches')

    assert response.status == 200
    assert response.url.path == login_path


@pytest.mark.usefixtures('setup_tables_and_data')
async def test_update_switch_without_login(client, login_path):
    response = await client.post('/zbs/switches/1', data={'version': 'some_shit'})

    assert response.status == 200
    assert response.url.path == login_path


@pytest.mark.parametrize(
    'switch_title, expected_result',
    [
        ('switch1', True),
        ('switch2', True),
        ('switch6', False),
        ('switch8', False),
        ('switch1488', False),
    ],
)
@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test_switches_list(client, switch_title, expected_result):
    response = await client.get('/zbs/switches')

    content = await response.content.read()

    assert (switch_title in content.decode('utf-8')) is expected_result


@pytest.mark.parametrize(
    'switch_title, expected_result',
    [
        ('switch1', True),
        ('switch2', True),
        ('switch6', True),
        ('switch8', True),
        ('switch1488', False),
    ],
)
@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test_switches_list__show_hidden(client, switch_title, expected_result):
    response = await client.get('/zbs/switches?show_hidden=True')

    content = await response.content.read()

    assert (switch_title in content.decode('utf-8')) is expected_result


@pytest.mark.parametrize(
    'group_title, switch_title, expected_result',
    [('', 'switch1', True), ('group1', 'switch1', True), ('group3', 'switch1', False)],
)
@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test_switches_list_filter_by_group(client, group_title, switch_title, expected_result):
    response = await client.get(f'/zbs/switches?group={group_title}')

    content = await response.content.read()

    assert (switch_title in content.decode('utf-8')) is expected_result


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test_switch_detail(client, switch):
    response = await client.get('/zbs/switches/1')

    content = await response.content.read()

    assert switch.name in content.decode('utf-8')


@pytest.mark.usefixtures('setup_tables_and_data', 'login')
async def test_switch_add_get_method(client):
    response = await client.get('/zbs/switches/add')
    content = await response.content.read()

    assert 'Flag adding' in content.decode('utf-8')


@freeze_time(datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc))
@pytest.mark.usefixtures('setup_tables_and_data')
async def test_switch_add_post_method(
    client, db_conn_acquirer, login, create_switch_data_factory, switch_to_json_factory,
):
    switch_data = create_switch_data_factory(
        deleted_at=datetime.datetime(2020, 4, 15, tzinfo=local_timezone()).isoformat(),
    )

    response = await client.post('/zbs/switches/add', data=switch_data)
    content = await response.content.read()
    async with db_conn_acquirer() as conn:
        result = await conn.execute(switches.select().where(switches.c.name == switch_data['name']))
        created_switch = await result.first()

    assert response.status == HTTPOk.status_code
    assert 'Switches list' in content.decode('utf-8')
    assert switch_to_json_factory(created_switch) == switch_data
    assert created_switch.created_at == datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc)


@pytest.mark.parametrize(
    ('blank_field', 'error_message'),
    [('name', 'Empty name is not allowed.'), ('groups', 'At least one group is required.')],
)
@pytest.mark.usefixtures('setup_tables_and_data')
async def test_switch_add_blank_fields_not_allowed(blank_field, error_message, client, login):
    switch_data = {
        'name': 'switch-1337',
        'is_active': True,
        'groups': 'group',
        'version': 1,
        'comment': 'Hi!',
        blank_field: '',
    }

    response = await client.post('/zbs/switches/add', data=switch_data)
    content = await response.content.read()
    content_decoded = content.decode('utf-8')

    assert 'Flag adding' in content_decoded
    assert error_message in content_decoded


@pytest.mark.usefixtures('setup_tables_and_data')
async def test_switch_get(client, login, db_conn_acquirer):
    response = await client.get('/zbs/switches/1')
    content = (await response.content.read()).decode('utf-8')

    assert 'switch1' in content


@pytest.mark.usefixtures('setup_tables_and_data')
@pytest.mark.freeze_time(datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc))
async def test_switch_get__deleted(client, login, db_conn_acquirer):
    response = await client.get('/zbs/switches/6')
    content = (await response.content.read()).decode('utf-8')

    assert 'Oops! this switch was &#34;deleted&#34;.' in content
    assert 'switch6' not in content


@pytest.mark.usefixtures('setup_tables_and_data')
async def test_switch_update(client, login, switch, db_conn_acquirer):
    with freeze_time('2020-08-15'):
        await client.post('/zbs/switches/1', data={'is_active': False, 'groups': 'group1, group2'})

    async with db_conn_acquirer() as conn:
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


@pytest.mark.usefixtures('setup_tables_and_data')
@pytest.mark.freeze_time(datetime.datetime(2020, 5, 1, tzinfo=datetime.timezone.utc))
async def test_switch_soft_delete(client, login, switch, db_conn_acquirer):
    response = await client.get('/zbs/switches')
    content = await response.content.read()
    assert 'switch7' in content.decode('utf-8')

    await client.get('/zbs/switches/7/delete')
    response = await client.get('/zbs/switches')
    content = await response.content.read()
    async with db_conn_acquirer() as conn:
        deleted_switch = await (await conn.execute(switches.select().where(
            switches.c.id == 7,
        ))).first()

    assert 'switch7' not in content.decode('utf-8')
    assert deleted_switch.deleted_at == utc_now() + datetime.timedelta(days=settings.flag_ttl_days)


@pytest.mark.usefixtures('setup_tables_and_data')
async def test_resurrect_switch(client, login, switch):
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
        'deleted_at': None,
        'groups': 'group1',
        'version': 4,
    }
    response = await client.post('/zbs/switches/add', data=switch_data)
    content = await response.content.read()

    assert 'switch3' in content.decode('utf-8')


async def test_switches_copy_without_authorization(setup_tables_and_data, client, login_path):
    response = await client.post('/zbs/switches/copy')

    assert response.status == 200
    assert response.url.path == login_path


@pytest.mark.parametrize(
    ('http_get_arguments', 'old_switch_is_active_expected', 'expected_updated_at'),
    [
        ('', True, datetime.datetime(2020, 4, 15, tzinfo=datetime.timezone.utc)),
        (
            '?update_existing=true',
            False,
            datetime.datetime(2020, 10, 15, tzinfo=datetime.timezone.utc),
        ),
    ],
)
@freeze_time(datetime.datetime(2020, 10, 15, tzinfo=datetime.timezone.utc))
@pytest.mark.usefixtures(
    'setup_tables_and_data', 'login', 'get_switches_data_mocked_existing_switch',
)
async def test_switches_copy_existing_switch_foo(
    client, db_conn_acquirer,
    http_get_arguments,
    old_switch_is_active_expected,
    expected_updated_at,
):
    response = await client.post(f'/zbs/switches/copy{http_get_arguments}')
    async with db_conn_acquirer() as conn:
        result = await conn.execute(switches.count())
        switches_count = await result.first()
        switches_count = switches_count[0]
        result = await conn.execute(switches.select().where(switches.c.name == 'switch7'))
        old_switch = await result.first()

    assert response.status == 200
    assert switches_count == 8
    assert old_switch.is_active == old_switch_is_active_expected
    assert old_switch.updated_at == expected_updated_at


@pytest.mark.usefixtures('setup_tables_and_data', 'login', 'get_switches_data_mocked_new_switch')
async def test_switches_copy_new_switch(client, db_conn_acquirer):
    response = await client.post('/zbs/switches/copy')
    async with db_conn_acquirer() as conn:
        result = await conn.execute(
            switches.select().where(switches.c.name == 'extremely_new_switch'),
        )
        new_switch = await result.first()

    assert response.status == 200
    assert new_switch is not None
    assert new_switch.name == 'extremely_new_switch'


@pytest.mark.parametrize('switch_name', ['switch', ' switch', 'switch ', ' switch '])
@pytest.mark.usefixtures('setup_tables_and_data')
async def test_switch_strip_spaces(
    client, db_conn_acquirer, login, create_switch_data_factory, switch_name,
):
    switch_data = create_switch_data_factory(name=switch_name)

    await client.post('/zbs/switches/add', data=switch_data)
    async with db_conn_acquirer() as conn:
        result = await conn.execute(switches.select().order_by(desc('id')))
        created_switch = await result.first()

    assert created_switch.name == 'switch'


@pytest.mark.usefixtures('setup_tables_and_data', 'login', 'badge_mask_id_patch')
async def test_switch_detail_svg_badge(client, switch):
    svg_badge_url = str(client.make_url(f'/api/v1/switches/{switch.id}/svg-badge'))
    expected_svg_badge = get_switch_badge_svg(
        hostname=f'{client.host}:{client.port}', switch=switch,
    )
    expected_markdown_badge = get_switch_markdown_badge(
        request=make_mocked_request(method='GET', path=svg_badge_url, app=client.app),
        switch=switch,
    )

    response = await client.get('/zbs/switches/1')
    content = await response.content.read()
    content = content.decode('utf-8')

    assert switch.name in content
    assert 'block-svg-badge' in content
    assert 'copy-md-badge-btn' in content
    assert 'md-badge' in content
    assert expected_svg_badge in content
    assert expected_markdown_badge in content
