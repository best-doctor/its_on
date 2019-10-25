import pytest
from multidict import MultiDict


async def test_users_table_available(tables_and_data, client, login):
    response = await client.get('/zbs/switches')

    assert 'Users' in await response.text()


@pytest.mark.parametrize('user_login, user_pass, expected_result', [
    ('admin', 'password', 200),  # superuser
    ('user1', 'password', 403),
])
async def test_users_available_to_editing_only_for_superuser(
    tables_and_data,
    client,
    user_login,
    user_pass,
    expected_result,
):
    await client.post('/zbs/login', data={'login': user_login, 'password': user_pass})

    response = await client.get('/zbs/users/1')

    assert response.status == expected_result


@pytest.mark.parametrize('user_login, user_pass, flag_to_edit_id, expected_status_code', [
    ('admin', 'password', 7, 200),  # superuser can edit any flags
    ('user1', 'password', 4, 403),
    ('user1', 'password', 5, 403),
    ('user1', 'password', 6, 403),
    ('user1', 'password', 7, 200),
])
async def test_user_switches_editing(
    tables_and_data,
    client,
    user_login,
    user_pass,
    flag_to_edit_id,
    expected_status_code,
):
    await client.post('/zbs/login', data={'login': user_login, 'password': user_pass})

    response = await client.get(f'/zbs/switches/{flag_to_edit_id}')

    assert response.status == expected_status_code


@pytest.mark.parametrize('login, password, expected_response_code', [
    ('admin', 'password', 200),
    ('user1', 'password', 403),
])
async def test_only_superuser_can_edit_user_switches(tables_and_data, login, password, expected_response_code, client):
    await client.post('/zbs/login', data={'login': login, 'password': password})

    response = await client.post('/zbs/users/2', data=MultiDict([('switch_ids', 4), ('is_superuser', False)]))

    assert response.status == expected_response_code


async def test_add_switches_for_edit_to_user(tables_and_data, client):
    await client.post('/zbs/login', data={'login': 'admin', 'password': 'password'})
    await client.post('/zbs/users/2', data=MultiDict([('switch_ids', 4), ('switch_ids', 5), ('is_superuser', False)]))
    await client.get('/zbs/logout')
    await client.post('/zbs/login', data={'login': 'user1', 'password': 'password'})

    response = await client.get('/zbs/switches/4')
    response1 = await client.get('/zbs/switches/5')

    assert response.status == 200
    assert response1.status == 200


async def test_remove_switches_for_user_editing(tables_and_data, login, client):
    await client.post('/zbs/login', data={'login': 'admin', 'password': 'password'})
    await client.post('/zbs/users/2', data=MultiDict([('switch_ids', 4), ('is_superuser', False)]))
    await client.get('/zbs/logout')
    await client.post('/zbs/login', data={'login': 'user1', 'password': 'password'})

    response = await client.get('/zbs/switches/4')
    response1 = await client.get('/zbs/switches/5')

    assert response.status == 200
    assert response1.status == 403
