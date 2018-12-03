# Osiris: Build log aggregator.

"""OCP API schema."""

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema


class OCP(object):

    # TODO: include oc env as well?
    def __init__(self,
                 name: str,
                 namespace: str,
                 image: str,
                 kind: int):

        self.kind = kind

        self.name = name
        self.namespace = namespace

        self.image = image


class OCPSchema(Schema):

    kind = fields.String()

    name = fields.String()
    namespace = fields.String()

    image = fields.Url()

    @post_load
    def make_build(self, data: dict) -> OCP:
        return OCP(**data)
