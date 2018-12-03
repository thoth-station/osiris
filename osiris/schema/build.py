# Osiris: Build log aggregator.

"""Build API schema."""

from marshmallow import fields
from marshmallow import post_load
from marshmallow import Schema

from osiris import DEFAULT_OC_LOG_LEVEL
from osiris.schema.ocp import OCP, OCPSchema


# @proto
# class BuildLog(object):
#
#     def __init__(self, url: str):
#
#         self.url = url
#
#     def curl(self) -> str:
#
#         pass


class BuildInfo(object):

    def __init__(self,
                 build_id: str,
                 build_status: str,
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


class BuildInfoSchema(Schema):

    build_id = fields.String(required=True)
    build_status = fields.String(required=True)

    build_url = fields.Url()
    build_log_url = fields.Url()

    ocp_info = fields.Nested(OCPSchema)

    log_level = fields.Integer()

    @post_load
    def make_build_info(self, data: dict) -> BuildInfo:
        return BuildInfo(**data)
