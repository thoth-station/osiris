# Osiris: Build log aggregator.

"""Authentication API schema."""

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema

from osiris import DEFAULT_OC_PROJECT


class Login(object):

    def __init__(self, token: str, context: str = '0.0.0.0', namespace: str = None,
                 host: str = None, port: str = None, url: str = None, user: str = None):
        self.token: str = token

        self.context: str = context
        self.namespace: str = namespace

        self.host: str = host
        self.port: str = port
        self.url: str = url

        self.user: str = user


class LoginSchema(Schema):

    token = fields.String(required=True)

    context = fields.String(
        required=False, default='0.0.0.0')  # if not provided, use localhost
    namespace = fields.String(
        required=False, default=DEFAULT_OC_PROJECT, allow_none=True)

    host = fields.String(allow_none=True)
    port = fields.String(allow_none=True)
    url = fields.Url(allow_none=True)

    user = fields.String(allow_none=True)

    @post_load
    def make_user(self, data: dict) -> Login:
        return Login(**data)
