"""add environments

Revision ID: a7c1e4d92b58
Revises: f3cd679c723f
Create Date: 2026-09-30 17:30:00.000000

"""
import sqlalchemy as sa
from alembic import op

from its_on.utils import AwareDateTime

# revision identifiers, used by Alembic.
revision = 'a7c1e4d92b58'
down_revision = 'f3cd679c723f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'environments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', AwareDateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.CheckConstraint(r"name ~ '^[a-z0-9]+(-[a-z0-9]+)*$'", name='environment_name_slug'),
    )
    op.create_table(
        'switch_environments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('switch_id', sa.Integer(), nullable=False),
        sa.Column('environment_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['switch_id'], ['switches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('switch_id', 'environment_id', name='switch_environment_unique'),
    )
    op.create_index('idx_switch_environments_switch_id', 'switch_environments', ['switch_id'])
    op.create_index('idx_switch_environments_environment_id', 'switch_environments', ['environment_id'])


def downgrade():
    op.drop_index('idx_switch_environments_environment_id', table_name='switch_environments')
    op.drop_index('idx_switch_environments_switch_id', table_name='switch_environments')
    op.drop_table('switch_environments')
    op.drop_table('environments')
