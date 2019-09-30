from marshmallow import Schema, fields


class LoginPostRequestSchema(Schema):
    login = fields.Str()
    password = fields.Str()
