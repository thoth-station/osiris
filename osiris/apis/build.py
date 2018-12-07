# Osiris: Build log aggregator.

"""Namespace: build"""

from http import HTTPStatus

from flask import request

from flask_restplus import fields
from flask_restplus import Namespace
from flask_restplus import Resource

from osiris import DEFAULT_OC_LOG_LEVEL

from osiris.aggregator import build_aggregator

from osiris.apis.model import response

from osiris.response import request_accepted
from osiris.response import request_ok

from osiris.schema.build import BuildInfo, BuildInfoSchema
from osiris.schema.build import BuildInfoPagination, BuildInfoPaginationSchema


api = Namespace(name='build', description="Namespace for build triggers.")


build_fields = api.model('build_fields', {
    'build_id': fields.String(
        required=True,
        description="Unique build identification.",
        example="user-api-42-build"
    ),
    'build_url': fields.Url(
        required=False,
        description="URL to the OCP pod.",
    ),
    'build_status': fields.String(
        required=True,
        description="Status of the build.",
        example="COMPLETED"
    ),
    'build_log_url': fields.Url(
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


# status

@api.route('/status/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildStatusResource(Resource):
    """Build status endpoint."""

    # noinspection PyMethodMayBeStatic
    def get(self, build_id):
        """Return status of the given build."""

        _, build_info = build_aggregator.retrieve_build_log(build_id)

        return request_ok(payload={
            'build_status': build_info.build_status
        })


# info

@api.route('/info/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildInfoResource(Resource):
    """Build information endpoint."""

    # noinspection PyMethodMayBeStatic
    @api.marshal_with(build_response)
    @api.response(code=HTTPStatus.OK,
                  description="Retrieve stored information about build "
                              "specified by unique build id.",
                  model=build_response)
    def get(self, build_id):
        """Return complete information stored about given build."""

        schema = BuildInfoSchema()
        _, build_info = build_aggregator.retrieve_build_log(build_id)

        return request_ok(payload=schema.dump(build_info))


@api.route('/info/page', defaults={'page': 1})
@api.route('/info/page/<int:page>')
class BuildInfoListingResource(Resource):
    """Build information endpoint."""

    # noinspection PyMethodMayBeStatic
    @api.response(code=HTTPStatus.OK,
                  description="Paginate build information documents."
                  )
    def get(self, page):
        """Paginate build information documents stored in Ceph."""

        schema = BuildInfoPaginationSchema()
        page: BuildInfoPagination = build_aggregator.paginate_build_info(page)

        return request_ok(payload=schema.dump(page))


# logs

@api.route('/logs/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildLogResource(Resource):
    """Build log endpoint."""

    # noinspection PyMethodMayBeStatic
    @api.marshal_with(response)
    @api.response(code=HTTPStatus.OK,
                  description="Retrieve stored build logs"
                              "for given build id.",
                  )
    @api.doc(responses={
        s.value: s.description for s in [
            HTTPStatus.OK,
            HTTPStatus.BAD_REQUEST
        ]})
    def get(self, build_id):
        """Return logs stored by the given build."""

        build_log, = build_aggregator.retrieve_build_log(build_id, log_only=True)

        # FIXME: return the whole doc or just the build log?
        return request_ok(
            payload=build_log
        )


# triggers

@api.route('/init/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildInitiatedResource(Resource):
    """Receiver hook for initiated builds."""

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build initiation hook."""
        return request_accepted()


@api.route('/start/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildStartedResource(Resource):
    """Receiver hook for started builds."""

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build start hook."""
        return request_accepted()


@api.route('/finish/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildCompletedResource(Resource):
    """Receiver hook for completed builds.

    When the build is marked completed and this endpoint
    is triggered, the aggregator will automatically gather
    logs for the given build.
    """

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build completion hook."""

        log_level: int = request.args.get('log_level', DEFAULT_OC_LOG_LEVEL)

        # TODO: run all of the following ops asynchronously

        # get build log
        build_log: str = build_aggregator.curl_build_log(build_id, log_level)

        # TODO: get all additional information according to BuildInfoSchema
        build_info = BuildInfo(
            build_id, build_status='COMPLETED'
        )

        build_schema = BuildInfoSchema()

        build_doc = build_schema.dump(build_info)
        build_doc.data['build_log'] = build_log

        # store in Ceph
        _ = build_aggregator.store_build_log(build_doc.data)

        return request_accepted()
