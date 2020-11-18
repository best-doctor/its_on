from marshmallow import Schema, fields


class SwitchListRequestSchema(Schema):
    group = fields.Str(description='group', required=True)
    version = fields.Int()


class SwitchListResponseSchema(Schema):
    count = fields.Integer()
    result = fields.List(fields.String)


class SwitchScheme(Schema):
    name = fields.String()
    is_active = fields.Boolean()
    is_hidden = fields.Boolean()
    group = fields.String()
    groups = fields.List(fields.String)
    version = fields.String()
    comment = fields.String()


class SwitchFullListResponseSchema(Schema):
    result = fields.List(fields.Nested(SwitchScheme))
