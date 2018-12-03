# Osiris: Build log aggregator.

"""Namespace: build"""

from http import HTTPStatus

import shlex
import subprocess

from flask import request

from flask_restplus import fields
from flask_restplus import Namespace
from flask_restplus import Resource

from osiris import DEFAULT_OC_LOG_LEVEL

from osiris.apis.model import response

from osiris.response import bad_request
from osiris.response import request_accepted
from osiris.response import request_ok

from osiris.schema.build import BuildInfoSchema

api = Namespace(name='build', description="Namespace for build triggers.")

build_fields = api.model('build_fields', {
    'build_id': fields.String(
        required=True,
        description="Unique build identification.",
        example="user-api-42-build"
    ),
    'build_url': fields.String(
        required=False,
        description="URL to the OCP pod.",
    ),
    'build_status': fields.String(
        required=True,
        description="Status of the build.",
        example="COMPLETED"
    ),
    'build_log_url': fields.String(
        required=False,
        description="URL to build logs.",
    ),
    'ocp_info': fields.Raw(
        required=True,
        description="OCP build-related information.",
    ),
})

build_response = api.inherit('build_response', response, {
    'payload': fields.Nested(build_fields)
})


@api.route('/status/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildStatus(Resource):
    """Build status endpoint."""

    # noinspection PyMethodMayBeStatic
    def get(self, build_id):
        """Return status of the given build."""
        return request_ok()


@api.route('/info/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildInfo(Resource):
    """Build information endpoint."""

    # noinspection PyMethodMayBeStatic
    def get(self, build_id):
        """Return complete information stored about given build."""

        schema = BuildInfoSchema()
        build_info = ...

        return request_ok(payload=schema.dump(build_info))


@api.route('/logs/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildLog(Resource):
    """Build log endpoint."""

    # noinspection PyMethodMayBeStatic
    @api.doc(responses={
        s.value: s.description for s in [
            HTTPStatus.OK,
            HTTPStatus.BAD_REQUEST
        ]})
    def get(self, build_id):
        """Return logs stored by the given build."""

        # optionally provided via url argument
        log_level = request.args.get('log_level', DEFAULT_OC_LOG_LEVEL)

        log_command = shlex.split(
            f"oc logs {build_id} --loglevel {log_level}"
        )

        proc = subprocess.Popen(log_command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        out, err = proc.communicate()
        ret_code = proc.wait()

        if ret_code > 0:
            return bad_request(  # TODO: Correct response w.r.t ret_code
                output=err.decode('utf-8') or None,
                errors=err.decode('utf-8') or None
            )

        return request_ok(
            payload={'build_log': out.decode('utf-8')}
        )


@api.route('/init/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildInitiated(Resource):
    """Receiver hook for initiated builds."""

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build initiation hook."""
        return request_accepted()


@api.route('/start/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildStarted(Resource):
    """Receiver hook for started builds."""

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build start hook."""
        return request_accepted()


@api.route('/finish/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildCompleted(Resource):
    """Receiver hook for completed builds.

    When the build is marked completed and this endpoint
    is triggered, the aggregator will automatically gather
    logs for the given build.
    """

    # noinspection PyMethodMayBeStatic
    def get(self, build_id):
        """Check whether given build is completed."""
        return request_ok()

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build completion hook."""
        return request_accepted()
