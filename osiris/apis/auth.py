# Osiris: Build log aggregator.

"""Namespace: auth"""

from http import HTTPStatus
from typing import Union

from flask_restplus import fields
from flask_restplus import Namespace
from flask_restplus import Resource

from marshmallow import ValidationError

from osiris.apis.model import response

from osiris.response import request_ok

from osiris.exceptions import OCError
from osiris.utils import execute_command

from werkzeug.exceptions import HTTPException, InternalServerError


api = Namespace(name='auth',
                description="Namespace for API authorization.",
                validate=True)


@api.errorhandler(OCError)
@api.errorhandler(ValidationError)
def propagate_login_error(
        error: Union[OCError, ValidationError]):
    """Propagate login error to the global app error handler."""
    raise error  # re-raise


@api.errorhandler(HTTPException)
@api.errorhandler(InternalServerError)
def propagate_internal_server_error(
        error: Union[HTTPException, InternalServerError]):
    """Propagate internal server error to the global app error handler."""
    raise error  # re-raise


@api.errorhandler(Exception)
def propagate_unknown_exception(error: Exception):
    """Propagate unknown exception to the global app error handler."""
    raise error  # re-raise


login_fields = api.model('login_fieds', {
    'host': fields.String(
        required=False,
        description="Host the user is currently logged into.",
        example="<host>:<port>"
    ),
    'context': fields.String(
        required=False,
        description="Current context.",
        example="<username>"
    ),
    'namespace': fields.String(
        required=False,
        description="Current user.",
        example="<username>"
    ),
    'login_status': fields.String(
        required=True,
        description="Login status."
                    "One of [AUTHENTICATED, NOT AUTHENTICATED]",
        example="AUTHENTICATED"
    ),
})

login_response = api.inherit('login_response', response, {
    'payload': fields.Nested(login_fields)
})


login_request = api.model('login_request', {
    'server': fields.String(
        required=True,
        description="Server to log into.",
        example="<host>"
    ),
    'token': fields.String(
        required=True,
        description="Session or service token.",
        example="<token>"
    )
})


@api.route("/status")
class AuthStatusResource(Resource):
    """Authentication endpoint."""

    @api.marshal_with(login_response)
    @api.doc(responses={
        s.value: s.description for s in [
            HTTPStatus.OK,
        ]})
    def get(self):
        """Check whether current session is authorized."""
        context = None
        login_status = 'AUTHENTICATED'

        try:
            context = _oc_show_context()
        except OCError:
            login_status = 'NOT AUTHENTICATED'

        payload = {
            'context': context,
            'login_status': login_status
        }

        return request_ok(payload=payload)


def _oc_show_context() -> str:
    """Show current OC context."""
    context: bytes
    context, err, ret_code = execute_command("oc whoami --show-context")

    if ret_code > 0:
        raise OCError(ret_code, payload=err.decode('utf-8'))

    return context.decode('utf-8').strip()


def _oc_show_token() -> str:
    """Show current OC token."""
    token: bytes
    token, err, ret_code = execute_command("oc whoami --show-token")

    if ret_code > 0:
        raise OCError(ret_code, payload=err.decode('utf-8'))

    return token.decode('utf-8').strip()
