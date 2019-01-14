# Osiris: Build log aggregator.

"""Build API schema."""

from typing import List

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema

from osiris import DEFAULT_OC_LOG_LEVEL
from osiris.schema.ocp import OCP, OCPSchema

from kubernetes.client.models.v1_event import V1Event as Event


class BuildLog(object):

    def __init__(self, raw: str):

        self.data = raw


class BuildInfo(object):

    def __init__(self,
                 build_id: str = None,
                 build_status: str = None,
                 build_url: str = None,
                 build_log_url: str = None,
                 ocp_info: OCP = None,
                 log_level: int = None):

        self.build_id = build_id
        self.build_status = build_status

        self.build_url = build_url
        self.build_log_url = build_log_url

        self.ocp_info = ocp_info

        self.log_level = log_level or DEFAULT_OC_LOG_LEVEL

    @classmethod
    def from_event(cls, event: Event, build_id: str = None, **kwargs):

        ocp = OCP.from_event(event)

        return cls(
            build_id=build_id or f"{event.involved_object.name}-build",
            build_status=event.reason,
            ocp_info=ocp,
            **kwargs
        )

    def build_complete(self) -> bool:
        return self.build_status == 'BuildCompleted'


class BuildInfoSchema(Schema):

    build_id = fields.String(required=True)
    build_status = fields.String(required=True)

    build_url = fields.Url(required=False)
    build_log_url = fields.Url(required=False)

    ocp_info = fields.Nested(OCPSchema, required=False)

    log_level = fields.Integer(required=False)

    @post_load
    def make_build_info(self, data: dict) -> BuildInfo:
        return BuildInfo(**data)


class BuildInfoPagination(object):

    RESULTS_PER_PAGE = 20

    def __init__(self,
                 build_info_list: List[BuildInfo] = None,
                 total: int = None,
                 has_next: bool = None,
                 has_prev: bool = None):

        self.build_info = build_info_list

        self.total = total
        self.has_next = has_next
        self.has_prev = has_prev


class BuildInfoPaginationSchema(Schema):

    build_info = fields.List(fields.Nested(BuildInfoSchema))

    total = fields.Integer(required=True)
    has_next = fields.Bool(required=False)
    has_prev = fields.Bool(required=False)
