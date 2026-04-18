from unittest.mock import AsyncMock

import pytest


@pytest.mark.parametrize(
    'path',
    ['/lullz', '/readyz', '/healthz'],
)
async def test_probe_get_ok(setup_tables_and_data, client, path):
    response = await client.get(path)
    assert response.status == 200
    assert await response.text() == 'ok'


@pytest.mark.parametrize(
    'path',
    ['/lullz', '/readyz', '/healthz'],
)
async def test_probe_options(setup_tables_and_data, client, path):
    response = await client.options(path)
    assert response.status == 204
    assert response.headers.get('Allow') == 'GET, OPTIONS'


async def test_readiness_db_failure(client, mocker):
    mocker.patch('its_on.probes.is_app_healthy', new=AsyncMock(return_value=False))

    response = await client.get('/readyz')
    assert response.status == 500
    assert await response.text() == 'error'
