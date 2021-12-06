from __future__ import annotations

import typing
from marshmallow import Schema, fields, validate


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
    version = fields.Int()
    comment = fields.Str()
    ttl = fields.Int(validate=validate.Range(min=1))
    jira_ticket = fields.Str()


class SwitchDetailAdminPostRequestSchema(BaseSwitchAdminPostRequestSchema):
    groups = SplitList(
        fields.Str(), validate=validate.Length(min=1, error='At least one group is required.'),
    )


class SwitchAddAdminPostRequestSchema(BaseSwitchAdminPostRequestSchema):
    name = fields.Str(validate=validate.Length(min=1, error='Empty name is not allowed.'))
    groups = SplitList(
        fields.Str(), validate=validate.Length(min=1, error='At least one group is required.'),
    )


class SwitchAddFromAnotherItsOnAdminPostRequestSchema(BaseSwitchAdminPostRequestSchema):
    name = fields.Str()
    groups = fields.List(fields.Str())
    is_hidden = fields.Boolean()


class SwitchCopyFromAnotherItsOnAdminPostRequestSchema(BaseSwitchAdminPostRequestSchema):
    name = fields.Str()
    groups = fields.List(fields.Str())
    is_hidden = fields.Boolean()
    created_at = fields.DateTime(required=False, allow_none=True)


class SwitchListAdminRequestSchema(Schema):
    group = fields.Str(required=False)
    show_hidden = fields.Boolean(missing=False)


class UserDetailPostRequestSchema(Schema):
    is_superuser = fields.Boolean()
    switch_ids = fields.Integer()
