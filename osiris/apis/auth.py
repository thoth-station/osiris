# Osiris: Build log aggregator.

"""Namespace: auth"""

from http import HTTPStatus

from flask_restplus import Namespace
from flask_restplus import Resource

from osiris.response import status_ok
from osiris.response import request_accepted
from osiris.response import request_unauthorized
from osiris.response import request_forbidden


api = Namespace(name='auth', description="Namespace for API authorization.")


@api.route("/status")
class UserAuthorized(Resource):
    """Authorization endpoint."""

    @api.doc(responses={
        HTTPStatus.OK.value: HTTPStatus.OK.phrase,
        HTTPStatus.UNAUTHORIZED.value: HTTPStatus.UNAUTHORIZED.description,
    })
    def get(self):
        """Check whether current session is authorized."""
        pass


@api.route("/authorize")
class Authorize(Resource):

    @api.doc(responses={
        HTTPStatus.ACCEPTED.value: HTTPStatus.ACCEPTED.phrase,
        HTTPStatus.BAD_REQUEST.value: HTTPStatus.BAD_REQUEST.description,
    })
    def put(self):
        """Authorize current session."""
        pass
