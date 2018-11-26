# Osiris: Build log aggregator.

"""Namespace: probes"""

from http import HTTPStatus

from flask_restplus import Namespace
from flask_restplus import Resource

from osiris.response import request_ok
from osiris.apis.models import response

api = Namespace(name='probes', description="Namespace for API health checks.")


@api.route('/liveness')
class Liveness(Resource):
    """Health check."""

    # noinspection PyMethodMayBeStatic
    @api.marshal_with(response)
    @api.response(HTTPStatus.OK.value, HTTPStatus.OK.phrase)
    def get(self):  # pragma: no cover
        """Health check."""
        return request_ok()


@api.route('/readiness')
class Readiness(Resource):
    """Readiness check.

    Checks Ceph storage availability.
    """
    # noinspection PyMethodMayBeStatic
    @api.marshal_with(response)
    @api.doc(responses={
        s.value: s.description for s in [
            HTTPStatus.OK,
            HTTPStatus.FORBIDDEN,
            HTTPStatus.UNAUTHORIZED
        ]})
    def get(self):  # pragma: no cover
        """Readiness check."""
        # TODO: check Ceph, for now return accepted
        return request_ok()
