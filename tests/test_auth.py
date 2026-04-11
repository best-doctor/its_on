from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp.test_utils import make_mocked_request
from keycloak import KeycloakError
from sqlalchemy import func

from auth.auth import get_login_context, get_or_create_user
from auth.utils import user_has_permission
from auth.keycloak import get_username_from_token, has_developer_role
from auth.models import permissions, users
from auth.enums import Permission
from its_on.app_keys import db_key
from its_on.config import settings

from its_on.main import init_gunicorn_app


# --- Unit: has_developer_role ---

@pytest.mark.parametrize(
    ('decoded_token', 'expected'),
    [
        ({'resource_access': {settings.OAUTH.CLIENT_ID: {'roles': ['developers']}}}, True),
        ({'resource_access': {settings.OAUTH.CLIENT_ID: {'roles': ['developers', 'viewer']}}}, True),
        ({'resource_access': {settings.OAUTH.CLIENT_ID: {'roles': ['viewer', 'admin']}}}, False),
        ({'resource_access': {settings.OAUTH.CLIENT_ID: {'roles': []}}}, False),
        ({'resource_access': {settings.OAUTH.CLIENT_ID: {}}}, False),
        ({'resource_access': {}}, False),
        ({'realm_access': {'roles': ['developers']}}, False),
        ({}, False),
    ],
    ids=[
        'has-developers-role',
        'developers-among-others',
        'only-other-roles',
        'empty-roles-list',
        'no-roles-key',
        'no-matching-client',
        'realm-only-ignored',
        'empty-token',
    ],
)
def test__has_developer_role__returns_expected(decoded_token, expected):
    assert has_developer_role(decoded_token) == expected


# --- Unit: get_username_from_token ---

@pytest.mark.parametrize(
    ('decoded_token', 'expected'),
    [
        ({'preferred_username': 'john'}, 'john'),
        ({'preferred_username': 'dev@example.com'}, 'dev@example.com'),
        ({}, None),
    ],
    ids=['plain-username', 'email-username', 'missing-username'],
)
def test__get_username_from_token__returns_expected(decoded_token, expected):
    assert get_username_from_token(decoded_token) == expected


# --- user_has_permission ---

@pytest.mark.usefixtures('setup_tables_and_data')
async def test__user_has_permission__false_when_session_missing(client, mocker):
    mocker.patch('auth.utils.authorized_userid', AsyncMock(return_value=None))
    request = make_mocked_request('GET', '/', app=client.app)

    result = await user_has_permission(request, Permission.SWITCHES_EDIT_ALL)

    assert result is False


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__user_has_permission__false_for_unknown_login(client, mocker):
    mocker.patch('auth.utils.authorized_userid', AsyncMock(return_value='nemo'))
    request = make_mocked_request('GET', '/', app=client.app)

    result = await user_has_permission(request, Permission.SWITCHES_EDIT_ALL)

    assert result is False


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__user_has_permission__false_without_matching_row(client, mocker):
    mocker.patch('auth.utils.authorized_userid', AsyncMock(return_value='user1'))
    request = make_mocked_request('GET', '/', app=client.app)

    result = await user_has_permission(request, Permission.SWITCHES_EDIT_ALL)

    assert result is False


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__user_has_permission__true_when_permission_exists(
    client, mocker, db_conn_acquirer,
):
    async with db_conn_acquirer() as conn:
        await conn.execute(
            permissions.insert().values(
                user_id=2,
                perm_name=Permission.SWITCHES_EDIT_ALL,
            ),
        )

    mocker.patch('auth.utils.authorized_userid', AsyncMock(return_value='user1'))
    request = make_mocked_request('GET', '/', app=client.app)

    result = await user_has_permission(request, Permission.SWITCHES_EDIT_ALL)

    assert result is True


# --- Unit: get_login_context ---

async def test__get_login_context__oauth_disabled():
    result = await get_login_context()

    assert result['use_oauth'] is False
    assert result['only_oauth'] is False
    assert 'error' not in result


async def test__get_login_context__with_error():
    result = await get_login_context(error='test error')

    assert result['error'] == 'test error'


# --- Integration: get_or_create_user ---

@pytest.mark.usefixtures('setup_tables_and_data')
async def test__get_or_create_user__returns_existing_user(client):
    db_engine = client.server.app[db_key]

    user = await get_or_create_user(db_engine, 'admin')

    assert user is not None
    assert user.login == 'admin'
    assert user.is_superuser is True


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__get_or_create_user__creates_new_user(client):
    db_engine = client.server.app[db_key]

    user = await get_or_create_user(db_engine, 'new_developer')

    assert user is not None
    assert user.login == 'new_developer'
    assert user.is_superuser is False
    assert user.disabled is False

    async with db_engine.acquire() as conn:
        perm_result = await conn.execute(
            permissions.select().where(permissions.c.user_id == user.id),
        )
        perm_rows = await perm_result.fetchall()

    assert len(perm_rows) == 1
    assert perm_rows[0].perm_name == Permission.SWITCHES_EDIT_ALL


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__get_or_create_user__does_not_duplicate(client, db_conn_acquirer):
    db_engine = client.server.app[db_key]

    await get_or_create_user(db_engine, 'new_developer')
    await get_or_create_user(db_engine, 'new_developer')

    async with db_conn_acquirer() as conn:
        query = users.select().where(
            users.c.login == 'new_developer',
        ).with_only_columns(func.count())
        count = await conn.scalar(query)

        perm_count = await conn.scalar(
            permissions.select()
            .where(permissions.c.perm_name == Permission.SWITCHES_EDIT_ALL)
            .with_only_columns(func.count()),
        )

    assert count == 1
    assert perm_count == 1


# --- Integration: Keycloak callback view ---

@pytest.fixture()
async def oauth_client(aiohttp_client):
    settings.OAUTH.IS_ENABLED = True
    app = await init_gunicorn_app()
    client = await aiohttp_client(app)
    yield client
    settings.OAUTH.IS_ENABLED = False


def _make_keycloak_mock(decoded_token):
    mock = MagicMock()
    mock.a_token = AsyncMock(
        return_value={'access_token': 'fake-token'},
    )
    mock.a_decode_token = AsyncMock(return_value=decoded_token)
    mock.auth_url = MagicMock(
        return_value='https://keycloak.test/auth',
    )
    return mock


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__keycloak_callback__creates_user_with_developer_role(
    oauth_client, mocker,
):
    decoded_token = {
        'preferred_username': 'keycloak_dev',
        'resource_access': {settings.OAUTH.CLIENT_ID: {'roles': ['developers']}},
    }
    mocker.patch(
        'auth.views.get_keycloak_openid',
        return_value=_make_keycloak_mock(decoded_token),
    )

    response = await oauth_client.get(
        '/oauth/callback', params={'code': 'test-code'},
    )

    assert response.status == 200
    assert response.url.path == '/zbs/switches'
    async with oauth_client.server.app[db_key].acquire() as conn:
        result = await conn.execute(
            users.select().where(users.c.login == 'keycloak_dev'),
        )
        user = await result.first()
    assert user is not None
    assert user.login == 'keycloak_dev'
    assert user.disabled is False


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__keycloak_callback__existing_user_login(
    oauth_client, mocker,
):
    decoded_token = {
        'preferred_username': 'admin',
        'resource_access': {settings.OAUTH.CLIENT_ID: {'roles': ['developers']}},
    }
    mocker.patch(
        'auth.views.get_keycloak_openid',
        return_value=_make_keycloak_mock(decoded_token),
    )

    response = await oauth_client.get(
        '/oauth/callback', params={'code': 'test-code'},
    )

    assert response.status == 200
    assert response.url.path == '/zbs/switches'


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__keycloak_callback__without_developer_role(
    oauth_client, mocker,
):
    decoded_token = {
        'preferred_username': 'viewer_user',
        'resource_access': {settings.OAUTH.CLIENT_ID: {'roles': ['viewer']}},
    }
    mocker.patch(
        'auth.views.get_keycloak_openid',
        return_value=_make_keycloak_mock(decoded_token),
    )

    response = await oauth_client.get(
        '/oauth/callback', params={'code': 'test-code'},
    )
    content = (await response.content.read()).decode('utf-8')

    assert 'Access denied: developers role required' in content


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__keycloak_callback__missing_code(oauth_client):
    response = await oauth_client.get('/oauth/callback')
    content = (await response.content.read()).decode('utf-8')

    assert 'Missing authorization code' in content


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__login_get__redirects_to_oauth_when_enabled(oauth_client):
    response = await oauth_client.get('/zbs/login', allow_redirects=False)

    assert response.status == 302
    assert response.headers['Location'].endswith('/oauth/auth')


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__login_get__returns_login_page_when_oauth_disabled(client):
    response = await client.get('/zbs/login')

    assert response.status == 200
    body = (await response.content.read()).decode('utf-8')
    assert 'Enter login' in body


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__keycloak_callback__token_exchange_fails(
    oauth_client, mocker,
):
    mock_keycloak = MagicMock()
    mock_keycloak.a_token = AsyncMock(
        side_effect=KeycloakError('connection error'),
    )
    mocker.patch(
        'auth.views.get_keycloak_openid',
        return_value=mock_keycloak,
    )

    response = await oauth_client.get(
        '/oauth/callback', params={'code': 'test-code'},
    )
    content = (await response.content.read()).decode('utf-8')

    assert 'Keycloak authentication failed' in content


@pytest.mark.usefixtures('setup_tables_and_data')
async def test__keycloak_callback__token_decode_fails(
    oauth_client, mocker,
):
    mock_keycloak = MagicMock()
    mock_keycloak.a_token = AsyncMock(
        return_value={'access_token': 'fake-token'},
    )
    mock_keycloak.a_decode_token = AsyncMock(
        side_effect=KeycloakError('invalid token'),
    )
    mocker.patch(
        'auth.views.get_keycloak_openid',
        return_value=mock_keycloak,
    )

    response = await oauth_client.get(
        '/oauth/callback', params={'code': 'test-code'},
    )
    content = (await response.content.read()).decode('utf-8')

    assert 'Token validation failed' in content
