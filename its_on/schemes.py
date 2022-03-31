from marshmallow import Schema, fields, validate, EXCLUDE


class SwitchListRequestSchema(Schema):
    group = fields.Str(description='group', required=True)
    is_active = fields.Boolean(description='is active')
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
    flag_url = fields.URL()


class SwitchFullListResponseSchema(Schema):
    result = fields.List(fields.Nested(SwitchScheme))


class SwitchRemoteDataSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    is_active = fields.Boolean()
    version = fields.Int()
    comment = fields.Str()
    ttl = fields.Int(validate=validate.Range(min=1))
    name = fields.Str()
    groups = fields.List(fields.Str())
    is_hidden = fields.Boolean()
    created_at = fields.Str(allow_none=True)
    updated_at = fields.Str(allow_none=True)


class RemoteSwitchesDataSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    result = fields.List(fields.Nested(SwitchRemoteDataSchema))
