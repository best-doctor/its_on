"""Added is_hidden column

Revision ID: 8fddaf01c35a
Revises: 667cfa92dfd5
Create Date: 2019-10-10 12:45:23.924489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8fddaf01c35a'
down_revision = '667cfa92dfd5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('switches', sa.Column('is_hidden', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('switches', 'is_hidden')
