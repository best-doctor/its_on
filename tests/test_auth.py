async def test_login_page(tables_and_data, client):
    response = await client.get('/zbs/login')

    assert 'ITS ON' in await response.text()
    assert 'Log in' in await response.text()


async def test_login(tables_and_data, client):
    response = await client.post('/zbs/login', data={'login': 'admin', 'password': 'password'})

    assert response.real_url.path == '/zbs/switches'


async def test_logout(tables_and_data, client):
    response = await client.get('/zbs/logout')

    assert response.real_url.path == '/zbs/login'
