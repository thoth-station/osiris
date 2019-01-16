# Osiris: Build log aggregator.

"""Namespace: auth"""

from http import HTTPStatus
from typing import Union

from flask_restplus import fields
from flask_restplus import Namespace
from flask_restplus import Resource

from marshmallow import ValidationError

from osiris import set_context
from osiris import set_token
from osiris import set_namespace

from osiris.apis.model import response

from osiris.response import request_accepted
from osiris.response import request_ok

from osiris.schema.auth import LoginSchema

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
class LoginStatusResource(Resource):
    """Authorization endpoint."""

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


@api.route("/login")
class LoginResource(Resource):

    @api.marshal_with(login_response,
                      code=HTTPStatus.ACCEPTED,
                      skip_none=True)
    @api.doc(
        responses={
            s.value: s.description for s in [
                HTTPStatus.ACCEPTED,
                HTTPStatus.BAD_REQUEST,
                HTTPStatus.FAILED_DEPENDENCY,
                HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED
            ]},
        body=login_request
    )
    def post(self):
        """Authorize current session.

        :raises OCError: In case of OC CLI failure.
        """
        schema = LoginSchema()
        login, errors = schema.load(api.payload)

        if errors:
            raise ValidationError(errors)

        login_output: str = _oc_login(login)

        # update user information
        login.context = _oc_show_context()
        namespace, host, user = login.context.split('/')

        login.namespace = namespace
        login.host, login.port = host.split(':')
        login.user = user
        login.token = _oc_show_token()

        # set Osiris environment
        set_token(login.token)
        set_context(login.context)
        set_namespace(login.namespace)

        return request_accepted(
            payload=schema.dump(login),
            output=login_output
        )


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


def _oc_login(login) -> str:
    """Login to the OpenShift cluster using OC CLI."""

    login_command = f"oc login {login.url} " \
                    f"--token {login.token} " \
                    f"--insecure-skip-tls-verify"

    out: bytes
    err: bytes

    out, err, ret_code = execute_command(login_command)

    if ret_code > 0:
        raise OCError(ret_code, payload=err.decode('utf-8'))

    if login.namespace:
        # switch to correct oc project
        _, err, ret_code = execute_command(f"oc project {login.namespace}")

        if ret_code > 0:
            raise OCError(ret_code, payload=err.decode('utf-8'))

    return out.decode('utf-8')
