# Osiris: Build log aggregator.

"""Build API schema."""

from datetime import datetime
from typing import List

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema

from osiris import DEFAULT_OC_LOG_LEVEL
from osiris.schema.ocp import OCP, OCPSchema

from kubernetes.client.models.v1_event import V1Event as Event

from thoth.common.helpers import _DATETIME_FORMAT_STRING
from thoth.common.helpers import datetime2datetime_str


class BuildLog(object):
    """BuildLog model."""

    def __init__(self, raw: str):
        """Initialize BuildLog model."""

        self.data = raw


class BuildInfo(object):
    """BuildInfo model."""

    def __init__(self,
                 build_id: str = None,
                 build_status: str = None,
                 build_url: str = None,
                 build_log_url: str = None,
                 ocp_info: OCP = None,
                 first_timestamp: datetime = None,
                 last_timestamp: datetime = None,
                 log_level: int = None):
        """Initialize BuildInfo model."""
        self.build_id = build_id
        self.build_status = build_status

        self.build_url = build_url
        self.build_log_url = build_log_url

        self.ocp_info = ocp_info

        self.first_timestamp = first_timestamp
        self.last_timestamp = last_timestamp

        self.log_level = log_level or DEFAULT_OC_LOG_LEVEL

    @classmethod
    def from_event(cls, event: Event, build_id: str = None, **kwargs):
        """Create BuildInfo model from kubernetes event."""
        ocp = OCP.from_event(event)

        return cls(
            build_id=build_id or event.involved_object.name,
            build_status=event.reason,
            first_timestamp=event.first_timestamp,
            last_timestamp=event.last_timestamp,
            ocp_info=ocp,
            **kwargs
        )

    def build_complete(self) -> bool:
        """Return whether build has completed.
        
        Failed builds are considered completed, too."""
        return self.build_status == 'BuildCompleted' or self.build_status == 'BuildFailed'


class BuildInfoSchema(Schema):
    """BuildInfo model schema."""

    build_id = fields.String(required=True)
    build_status = fields.String(required=True)

    build_url = fields.Url(required=False, allow_none=True)
    build_log_url = fields.Url(required=False, allow_none=True)

    ocp_info = fields.Nested(OCPSchema, required=False)

    first_timestamp = fields.DateTime(required=False)
    last_timestamp = fields.DateTime(required=False)

    log_level = fields.Integer(required=False)

    @post_load
    def make_build_info(self, data: dict) -> BuildInfo:
        """Make BuildInfo model from dictionary specification."""
        return BuildInfo(**data)


class BuildInfoPagination(object):
    """BuildInfoPagination model."""

    RESULTS_PER_PAGE = 20

    def __init__(self,
                 build_info_list: List[BuildInfo] = None,
                 total: int = None,
                 has_next: bool = None,
                 has_prev: bool = None):
        """Initialize BuildInfoPagination model."""
        self.build_info = build_info_list

        self.total = total
        self.has_next = has_next
        self.has_prev = has_prev


class BuildInfoPaginationSchema(Schema):
    """BuildInfoPagination model schema."""

    build_info = fields.Nested(BuildInfoSchema, many=True)

    total = fields.Integer(required=True)
    has_next = fields.Bool(required=False, default=False)
    has_prev = fields.Bool(required=False, default=False)
