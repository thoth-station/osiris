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
from osiris.response import bad_request

from osiris.schema.build import BuildInfo, BuildInfoSchema
from osiris.schema.build import BuildInfoPagination, BuildInfoPaginationSchema


api = Namespace(name='build', description="Namespace for build triggers.")


build_fields = api.model('build_fields', {
    'build_id': fields.String(
        required=True,
        description="Unique build identification.",
        example="user-api-42-build"
    ),
    'build_status': fields.String(
        required=True,
        description="Status of the build.",
        example="BuildStarted"
    ),
    'build_url': fields.Url(
        required=False,
        description="URL to the OCP pod.",
    ),
    'build_log_url': fields.Url(
        required=False,
        description="URL to build logs.",
    ),
    'ocp_info': fields.Raw(
        required=False,
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

        _, build_info = build_aggregator.retrieve_build_data(build_id)

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
        _, build_info = build_aggregator.retrieve_build_data(build_id)

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
        page: BuildInfoPagination = build_aggregator.paginate_build_data(page)

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

        build_log, = build_aggregator.retrieve_build_data(build_id, log_only=True)

        # FIXME: return the whole doc or just the build log?
        return request_ok(
            payload=build_log
        )


# triggers

@api.route('/started', defaults={'build_id': None})
@api.route('/started/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildStartedResource(Resource):
    """Receiver hook for started builds."""

    # noinspection PyMethodMayBeStatic
    @api.response(code=HTTPStatus.ACCEPTED,
                  description="Request has been accepted."
                              "Document will be stored in Ceph",
                  )
    @api.response(code=HTTPStatus.BAD_REQUEST,
                  description="Request could not be processed due to invalid data"
                              " or missing build identification."
                  )
    @api.expect(build_fields)
    def put(self, build_id: str = None):  # pragma: no cover
        """Trigger build start hook."""

        # TODO: run all of the following ops asynchronously
        errors = {}

        build_schema = BuildInfoSchema()
        build_data: dict = request.json

        if not any([build_data, build_id]):
            errors['build_data'] = "Invalid or missing build data."

        build_doc, validation_errors = build_schema.load(build_data, partial=True)
        build_doc['build_log'] = None

        if errors.get('build_id', None) and not build_id:
            # build_id is not provided at all
            errors['build_id'] = "Invalid or missing `build_id`."

        if not errors:  # validation errors other than build_id are permitted for now
            # store in Ceph
            build_aggregator.store_build_data(build_doc)

            return request_accepted(errors=validation_errors)

        else:
            errors.update(validation_errors)

            return bad_request(errors=errors)


@api.route('/completed', defaults={'build_id': None})
@api.route('/completed/<string:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildCompletedResource(Resource):
    """Receiver hook for completed builds.

    When the build is marked completed and this endpoint
    is triggered, the aggregator will automatically gather
    logs for the given build.
    """

    # noinspection PyMethodMayBeStatic
    @api.response(code=HTTPStatus.ACCEPTED,
                  description="Request has been accepted."
                              "Document will be stored in Ceph",
                  )
    @api.response(code=HTTPStatus.BAD_REQUEST,
                  description="Request could not be processed due to invalid data"
                              " or missing build identification."
                  )
    @api.expect(build_fields)
    def put(self, build_id: str = None):  # pragma: no cover
        """Trigger build completion hook."""
        log_level: int = request.args.get('log_level', DEFAULT_OC_LOG_LEVEL)

        build_schema = BuildInfoSchema()

        # TODO: run all of the following ops asynchronously
        # get stored build info
        _, build_info = build_aggregator.retrieve_build_data(build_id)

        build_data: dict = request.json

        build_doc, validation_errors = build_schema.load(build_data, partial=True)
        build_doc['build_log'] = None

        build_info.build_status = build_doc['build_status']

        # get build log
        build_log: str = build_aggregator.curl_build_log(build_id, log_level)

        build_doc, errors = build_schema.dump(build_info)
        build_doc['build_log'] = build_log
        build_doc['creation_timestamp'] = build_log
        build_doc['first_timestamp'] = build_log
        build_doc['last_timestamp'] = build_log

        # store in Ceph
        build_aggregator.store_build_data(build_doc)  # FIXME

        return request_accepted()
