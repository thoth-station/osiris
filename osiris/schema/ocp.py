# Osiris: Build log aggregator.

"""OCP API schema."""

import typing

from kubernetes.client.models.v1_event import V1Event as Event

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema


class OCP(object):

    # TODO: include oc env as well?
    def __init__(self,
                 kind: str,
                 name: str,
                 namespace: str,
                 link: str = None):

        self.kind = kind

        self.name = name
        self.namespace = namespace

        self.link = link

    @classmethod
    def from_event(cls, event: Event):
        kind = event.involved_object.kind
        name = event.involved_object.name
        namespace = event.involved_object.namespace

        link = event.metadata.self_link

        return cls(
            kind=kind,
            name=name,
            namespace=namespace,
            link=link
        )


class OCPSchema(Schema):

    kind = fields.String()

    name = fields.String()
    namespace = fields.String()

    link = fields.Url()

    @post_load
    def make_build(self, data: dict) -> OCP:
        return OCP(**data)
