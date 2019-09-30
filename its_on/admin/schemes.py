from marshmallow import Schema, fields


class SwitchDetailAdminPostRequestSchema(Schema):
    is_active = fields.Boolean()
    group = fields.Str()
    version = fields.Int()
    comment = fields.Str()
