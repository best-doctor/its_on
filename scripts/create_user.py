import click
import pathlib
import sys
import sqlalchemy as sa
from dynaconf import settings
from passlib.handlers.sha2_crypt import sha256_crypt

BASE_DIR = pathlib.Path(__file__).parent.parent
sys.path.append(str(BASE_DIR.absolute()))

from auth.models import users  # noqa


@click.command()
@click.option('--login', help='user login', required=True)
@click.option('--password', help='user password', required=True)
@click.option('--is_superuser', is_flag=True, default=False, help='user is superuser')
def create_user(login: str, password: str, is_superuser: bool) -> None:
    engine = sa.create_engine(settings.DATABASE.DSN)
    with engine.connect() as conn:
        conn.execute(
            users.insert(
                {
                    'login': login,
                    'passwd': sha256_crypt.hash(password),
                    'is_superuser': is_superuser,
                },
            ),
        )


if __name__ == '__main__':
    create_user()
