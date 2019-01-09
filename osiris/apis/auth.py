# Osiris: Build log aggregator.

"""Namespace: auth"""

from http import HTTPStatus

from flask_restplus import fields
from flask_restplus import Namespace
from flask_restplus import Resource

from osiris.apis.model import response

from osiris.response import request_accepted
from osiris.response import request_ok

from osiris.schema.auth import LoginSchema

from osiris.exceptions import OCError

from osiris.utils import execute_command


api = Namespace(name='auth',
                description="Namespace for API authorization.",
                validate=True)

login_fields = api.model('login_fieds', {
    'server': fields.String(
        required=False,
        description="Server the user is currently logged into.",
        example="<host>:<port>"
    ),
    'user': fields.String(
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

        out: bytes
        out, _, ret_code = execute_command("oc whoami --show-context")

        login_status = 'NOT AUTHENTICATED' if ret_code > 0 else 'AUTHENTICATED'

        server, user = "", ""

        try:
            server, user = out.decode('utf-8').strip().rsplit('/', 1)
        except ValueError:
            pass

        payload = {
            'server': server,
            'user': user,
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
        login = schema.load(api.payload).data

        login_command = f"oc login {login.server} --token {login.token}"

        out, err, ret_code = execute_command(login_command)

        if ret_code > 0:
            raise OCError(ret_code, payload=err.decode('utf-8'))

        # update user information

        user_data, _, ret_code = execute_command(f"oc whoami -c")
        server, user = user_data.split('/')

        login.server = server
        login.user = user

        return request_accepted(
            payload=schema.dump(login),
            output=out.decode('utf-8')
        )

