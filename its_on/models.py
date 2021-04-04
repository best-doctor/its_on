import datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from auth import models
from its_on.utils import AwareDateTime

metadata = sa.MetaData()


switches = sa.Table(
    'switches', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('is_active', sa.Boolean, default=True),
    sa.Column('is_hidden', sa.Boolean, default=False),
    sa.Column('name', sa.String(255), unique=True),
    sa.Column('group', sa.String(255)),
    sa.Column('groups', postgresql.ARRAY(sa.String(255))),
    sa.Column('version', sa.Integer, nullable=True),
    sa.Column('comment', sa.Text),
    sa.Column('created_at', AwareDateTime, default=lambda: datetime.datetime.utcnow(), nullable=True),
    sa.Column(
        'updated_at', AwareDateTime,
        default=lambda: datetime.datetime.utcnow(),
        onupdate=lambda: datetime.datetime.utcnow(),
        nullable=True,
    ),
)

sa.Index('idx_name_group_is_active', switches.c.name, switches.c.group, switches.c.is_active)
sa.Index('idx_name_group_version_is_active',
         switches.c.name, switches.c.group, switches.c.version, switches.c.is_active)


user_switches = sa.Table(
    'user_switches', metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey(models.users.c.id)),
    sa.Column('switch_id', sa.Integer, sa.ForeignKey(switches.c.id)),
    sa.UniqueConstraint('switch_id', 'user_id', name='user_switch_unique'),
)


switch_history = sa.Table(
    'switch_history', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('switch_id', sa.Integer, sa.ForeignKey(switches.c.id)),
    sa.Column('user_id', sa.Integer, sa.ForeignKey(models.users.c.id), nullable=False),
    sa.Column('new_value', sa.String(64), nullable=False),
    sa.Column(
        'changed_at',
        AwareDateTime,
        default=lambda: datetime.datetime.utcnow(),
        nullable=False
    ),
)
