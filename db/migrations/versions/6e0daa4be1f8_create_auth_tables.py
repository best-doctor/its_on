"""create auth tables

Revision ID: 6e0daa4be1f8
Revises: cb42b1c187d9
Create Date: 2019-09-26 09:17:12.642904

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6e0daa4be1f8'
down_revision = 'cb42b1c187d9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('login', sa.String(256), nullable=False),
        sa.Column('passwd', sa.String(256), nullable=False),
        sa.Column('is_superuser', sa.Boolean, nullable=False,
                  server_default='FALSE'),
        sa.Column('disabled', sa.Boolean, nullable=False,
                  server_default='FALSE'),

        # indices
        sa.PrimaryKeyConstraint('id', name='user_pkey'),
        sa.UniqueConstraint('login', name='user_login_key'),
    )

    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('perm_name', sa.String(64), nullable=False),

        # indices
        sa.PrimaryKeyConstraint('id', name='permission_pkey'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'],
                                name='user_permission_fkey',
                                ondelete='CASCADE'),
    )


def downgrade():
    op.drop_table('users')
    op.drop_table('permissions')
