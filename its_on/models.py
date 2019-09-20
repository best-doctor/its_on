import sqlalchemy as sa

from its_on.db_utils import metadata


switches = sa.Table(
    'switches', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('is_active', sa.Boolean, default=True),
    sa.Column('name', sa.String(255), unique=True),
    sa.Column('group', sa.String(255)),
    sa.Column('version', sa.Integer, nullable=True),
    sa.Column('comment', sa.Text),
)
