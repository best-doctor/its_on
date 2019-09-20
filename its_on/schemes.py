from marshmallow import Schema, fields


class SwitchListRequestSchema(Schema):
    group = fields.Str(description='group', required=True)
    version = fields.Int()


class SwitchListResponseSchema(Schema):
    count = fields.Integer()
    result = fields.List(fields.String)
