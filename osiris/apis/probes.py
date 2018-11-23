# Osiris: Build log aggregator.

"""Namespace: probes"""

from http import HTTPStatus

from flask_restplus import Namespace
from flask_restplus import Resource

from osiris.model import base_model
from osiris.response import status_ok
from osiris.response import request_accepted
from osiris.response import request_unauthorized
from osiris.response import request_forbidden

api = Namespace(name='probes', description="Namespace for API health checks.")


@api.route('/liveness')
class Liveness(Resource):
    """Health check."""
    # noinspection PyMethodMayBeStatic

    @api.marshal_with(base_model)
    @api.response(HTTPStatus.OK.value, HTTPStatus.OK.phrase, model=base_model)
    def get(self):  # pragma: no cover
        """Health check."""
        return status_ok()


@api.route('/readiness')
class Readiness(Resource):
    """Readiness check.

    Checks Ceph storage availability.
    """
    # noinspection PyMethodMayBeStatic
    @api.marshal_with(base_model)
    @api.doc(responses={
        HTTPStatus.OK.value: HTTPStatus.OK.phrase,
        HTTPStatus.UNAUTHORIZED.value: HTTPStatus.UNAUTHORIZED.description,
        HTTPStatus.FORBIDDEN.value: HTTPStatus.FORBIDDEN.description,
    })
    def get(self):  # pragma: no cover
        """Readiness check."""
        # TODO: check Ceph, for now return accepted
        return status_ok()

