"""Add groups column

Revision ID: 7fb20e27a402
Revises: 20ce9b327cdb
Create Date: 2020-04-27 16:43:27.667416

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7fb20e27a402'
down_revision = '20ce9b327cdb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('switches', sa.Column('groups', sa.ARRAY(sa.String(length=255)), nullable=True))
    op.execute("UPDATE switches SET groups = string_to_array(switches.group, '')")


def downgrade():
    op.execute('UPDATE switches SET "group" = groups[1]')
    op.drop_column('switches', 'groups')

