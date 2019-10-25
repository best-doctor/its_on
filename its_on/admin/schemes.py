from marshmallow import Schema, fields


class BaseSwitchAdminPostRequestSchema(Schema):
    is_active = fields.Boolean()
    group = fields.Str()
    version = fields.Int()
    comment = fields.Str()


class SwitchDetailAdminPostRequestSchema(BaseSwitchAdminPostRequestSchema):
    pass


class SwitchAddAdminPostRequestSchema(BaseSwitchAdminPostRequestSchema):
    name = fields.Str()


class UserDetailPostRequestSchema(Schema):
    is_superuser = fields.Boolean()
    switch_ids = fields.Integer()
