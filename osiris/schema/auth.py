# Osiris: Build log aggregator.

"""Authentication API schema."""

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema


class Login(object):

    def __init__(self, token: str, server: str = '0.0.0.0',
                 host: str = '', port: str = '', user: str = ''):
        self.token: str = token

        self.server: str = server

        self.host: str = host
        self.port: str = port

        self.user: str = user


class LoginSchema(Schema):

    token = fields.String(required=True)

    server = fields.String(required=False, default='0.0.0.0')  # if not provided, use localhost

    host = fields.String(allow_none=True)
    port = fields.String(allow_none=True)

    user = fields.String(allow_none=True)

    @post_load
    def make_user(self, data: dict) -> Login:
        return Login(**data)
