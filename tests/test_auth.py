async def test_login_page(tables_and_data, client):
    response = await client.get('/zbs')

    assert 'ITS ON' in await response.text()
    assert 'Log in' in await response.text()


async def test_login(tables_and_data, client):
    response = await client.post('/zbs', data={'login': 'admin', 'password': 'password'})

    assert response.real_url.path == '/admin/switches'


async def test_logout(tables_and_data, client):
    response = await client.get('/logout')

    assert response.real_url.path == '/zbs'
