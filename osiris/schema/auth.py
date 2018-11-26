# Osiris: Build log aggregator.

"""Authentication API schema."""

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema


class Login(object):

    def __init__(self, server: str, token: str, user: str = ''):
        self.server: str = server
        self.token: str = token
        self.user: str = user


class LoginSchema(Schema):

    server = fields.String(required=True)
    token = fields.String(required=True)
    user = fields.String()

    @post_load
    def make_user(self, data: dict) -> Login:
        return Login(**data)
