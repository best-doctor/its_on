"""Set is_hidden false

Revision ID: 4f13ecf8ddfd
Revises: 8fddaf01c35a
Create Date: 2019-10-10 12:51:48.467538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f13ecf8ddfd'
down_revision = '8fddaf01c35a'
branch_labels = None
depends_on = None


def upgrade():
    switches = sa.Table('switches', sa.MetaData(bind=op.get_bind()), autoload=True)

    op.get_bind().execute(
        switches.update().values(is_hidden=False),
    )


def downgrade():
    pass
