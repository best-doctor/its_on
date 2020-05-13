from __future__ import annotations

import typing
from marshmallow import Schema, fields


class SplitList(fields.List):
    def deserialize(
        self,
        value: typing.Any,
        attr: str = None,
        data: typing.Mapping[str, typing.Any] = None,
        **kwargs: typing.Any,
    ) -> typing.List[typing.Any]:
        value = value or ''
        values = filter(None, (item.strip() for item in value.split(',')))
        return super().deserialize(values, attr, data, **kwargs)


class BaseSwitchAdminPostRequestSchema(Schema):
    is_active = fields.Boolean()
    groups = SplitList(fields.Str())
    version = fields.Int()
    comment = fields.Str()


class SwitchDetailAdminPostRequestSchema(BaseSwitchAdminPostRequestSchema):
    pass


class SwitchAddAdminPostRequestSchema(BaseSwitchAdminPostRequestSchema):
    name = fields.Str()


class UserDetailPostRequestSchema(Schema):
    is_superuser = fields.Boolean()
    switch_ids = fields.Integer()
