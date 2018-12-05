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
class LoginStatusResource(Resource):
    """Authorization endpoint."""

    @api.doc(responses={
        s.value: s.description for s in [
            HTTPStatus.OK,
        ]})
    def get(self):
        """Check whether current session is authorized."""

        _, err, ret_code = execute_command("oc whoami")

        login_status = 'NOT AUTHENTICATED' if ret_code > 0 else 'AUTHENTICATED'

        return request_ok(payload={
            'login_status': login_status
        })


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
            output=out.decode('utf-8'),  # TODO: response following given schema
            payload=schema.dump(login)
        )

