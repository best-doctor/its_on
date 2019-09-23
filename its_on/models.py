import sqlalchemy as sa


metadata = sa.MetaData()


switches = sa.Table(
    'switches', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('is_active', sa.Boolean, default=True),
    sa.Column('name', sa.String(255), unique=True),
    sa.Column('group', sa.String(255)),
    sa.Column('version', sa.Integer, nullable=True),
    sa.Column('comment', sa.Text),
)

sa.Index('idx_group_is_active', switches.c.group, switches.c.is_active)
sa.Index('idx_group_version_is_active', switches.c.group, switches.c.version, switches.c.is_active)
