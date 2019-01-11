# Osiris: Build log aggregator.

"""Base API schema."""

from http import HTTPStatus

from marshmallow import fields
from marshmallow import Schema

from osiris import ABOUT
from osiris.utils import format_status_message


# Model: Status

class AppData(object):

    def __init__(self):
        self.name = ABOUT['__title__']
        self.version = ABOUT['__version__']


class AppDataSchema(Schema):

    name = fields.String(required=True)
    version = fields.String(required=True)


class Status(object):

    def __init__(self, status: HTTPStatus):
        self.code = status.value
        self.phrase = status.phrase
        self.description = status.description
        self.message = format_status_message(status)


class StatusSchema(Schema):

    code = fields.Integer(required=True)
    phrase = fields.String()
    description = fields.String()
    message = fields.String()


# Model: Base

class Base(object):

    def __init__(self, status: HTTPStatus):

        self.app_data = AppData()
        self.status = Status(status)

        self.output = None
        self.errors = None

        self.payload = None


class BaseSchema(Schema):

    app_data = fields.Nested(AppDataSchema)
    status = fields.Nested(StatusSchema)

    output = fields.Raw()  # oc-client output
    errors = fields.Raw()  # cli, parsing or other types of errors

    payload = fields.Raw()
