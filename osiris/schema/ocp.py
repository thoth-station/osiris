# Osiris: Build log aggregator.

"""OCP API schema."""

from kubernetes.client.models.v1_event import V1Event as Event

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema


class OCP(object):

    def __init__(self,
                 kind: str = None,
                 name: str = None,
                 namespace: str = None,
                 self_link: str = None):

        self.kind = kind

        self.name = name
        self.namespace = namespace

        self.self_link = self_link

    @classmethod
    def from_event(cls, event: Event):
        kind = event.involved_object.kind
        name = event.involved_object.name
        namespace = event.involved_object.namespace

        self_link = event.metadata.self_link

        return cls(
            kind=kind,
            name=name,
            namespace=namespace,
            self_link=self_link
        )


class OCPSchema(Schema):

    kind = fields.String(required=True)

    name = fields.String(required=True)
    namespace = fields.String(required=True)

    self_link = fields.String(required=False)

    @post_load
    def make_ocp(self, data: dict) -> OCP:
        return OCP(**data)
