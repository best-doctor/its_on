import pytest
from click.testing import CliRunner
from dynaconf import settings
from passlib.handlers.sha2_crypt import sha256_crypt

from auth.models import users
from scripts.create_user import create_user
from tests.helpers import get_engine


@pytest.mark.parametrize(
    'login, password, is_superuser',
    (
        ('user_login', 'user_password', True),
        ('user_login', 'user_password', False),
        ('', '', False),
    ),
)
def test_create_user(login, password, is_superuser, setup_tables):
    login = 'user123'
    password = 'qweqwe'
    is_superuser = True
    engine = get_engine(settings.DATABASE.DSN)

    runner = CliRunner()
    params = ['--login', login, '--password', password]
    if is_superuser:
        params.append('--is_superuser')
    runner.invoke(create_user, params)

    query = users.select().where(users.c.login == login)
    with engine.connect() as conn:
        result = conn.execute(query)
        user = result.fetchone()

    assert user.is_superuser is is_superuser
    assert sha256_crypt.verify(password, user.passwd)
