"""add environment to switch_history

Revision ID: b3d5f7a91c24
Revises: a7c1e4d92b58
Create Date: 2026-09-30 23:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b3d5f7a91c24'
down_revision = 'a7c1e4d92b58'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('switch_history', sa.Column('environment', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('switch_history', 'environment')
