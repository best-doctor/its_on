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
