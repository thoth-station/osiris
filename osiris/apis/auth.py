# Osiris: Build log aggregator.

"""Namespace: auth"""

from http import HTTPStatus

from flask_restplus import fields
from flask_restplus import Namespace
from flask_restplus import Resource

from osiris.apis.model import response

from osiris.response import bad_request
from osiris.response import request_accepted
from osiris.response import request_ok
from osiris.response import request_unauthorized

from osiris.schema.auth import LoginSchema

from osiris.utils import execute_command


api = Namespace(name='auth',
                description="Namespace for API authorization.",
                validate=True)

login_fields = api.model('login_fieds', {
    'server': fields.String(
        required=True,
        description="Server the user is currently logged into.",
        example="<host>:<port>"
    ),
    'user': fields.String(
        required=True,
        description="Current user.",
        example="<username>"
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
    # TODO: can it do any harm to return the token?
    'token': fields.String(
        required=True,
        description="Session or service token.",
        example="<token>"
    )
})


@api.route("/status")
class LoginStatus(Resource):
    """Authorization endpoint."""

    @api.doc(responses={
        s.value: s.description for s in [
            HTTPStatus.OK,
            HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED
        ]})
    def get(self):
        """Check whether current session is authorized."""

        logged_in = True  # TODO: Get current login status

        if logged_in:
            return request_ok(payload={
                'login_status': 'AUTHENTICATED'
            })

        else:
            return request_unauthorized()


@api.route("/login")
class Login(Resource):

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
        """Authorize current session."""
        schema = LoginSchema()
        login = schema.load(api.payload).data

        login_command = f"oc login {login.server} --token {login.token}"

        out, err, ret_code = execute_command(login_command)

        if ret_code > 0:
            return bad_request(
                output=out.decode('utf-8') or None,
                errors=err.decode('utf-8') or None
            )

        # update user information

        user_data, _, ret_code = execute_command(f"oc whoami -c")
        server, user = user_data.split('/')

        login.server = server
        login.user = user

        return request_accepted(
            output=out.decode('utf-8'),  # TODO: response following given schema
            payload=schema.dump(login)
        )

