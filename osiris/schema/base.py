# Osiris: Build log aggregator.

"""Base API schema."""

from http import HTTPStatus

from marshmallow import fields
from marshmallow import Schema

from osiris import ABOUT
from osiris.utils import format_status_message


# Model: Status

class Status(object):

    def __init__(self, status: HTTPStatus):
        self.code = status.value
        self.phrase = status.phrase
        self.description = status.description
        self.message = format_status_message(status)


class StatusSchema(Schema):

    code = fields.Integer()
    phrase = fields.String()
    description = fields.String()
    message = fields.String()


# Model: Base

class Base(object):

    def __init__(self, status: HTTPStatus):
        self.name = ABOUT['__title__']
        self.version = ABOUT['__version__']

        self.status = Status(status)


class BaseSchema(Schema):

    name = fields.String()
    version = fields.String()

    status = fields.Nested(StatusSchema)
