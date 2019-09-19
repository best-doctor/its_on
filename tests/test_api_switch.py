from its_on.main import init_app


async def test_switch(test_client):
    client = await test_client(init_app)
    response = await client.get('/api/v1/switch?group=test')
    response_json = await response.json()
    assert response.status == 200
    assert response_json == {'count': 0, 'result': []}


async def test_switch_without_params(test_client):
    client = await test_client(init_app)
    response = await client.get('/api/v1/switch')
    assert response.status == 422
