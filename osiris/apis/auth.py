# Osiris: Build log aggregator.

"""Namespace: auth"""

import shlex
import subprocess

from http import HTTPStatus

from flask_restplus import fields
from flask_restplus import Namespace
from flask_restplus import Resource

from osiris.apis.models import response

from osiris.response import request_ok
from osiris.response import bad_request
from osiris.response import request_accepted
from osiris.response import request_unauthorized

from osiris.schema.auth import LoginSchema


api = Namespace(name='auth',
                description="Namespace for API authorization.",
                validate=True)

login_response = api.inherit('login_response', response, {
    'user': fields.String
})


login_request = api.model('login_request', {
    'server': fields.String(
        required=True,
        description="Server to log into.",
        example="<host>:<port>"
    ),
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
            return request_ok(login_status='AUTHENTICATED')

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
        user = schema.load(api.payload)
        user_data = user.data

        login_command = shlex.split(
            f"oc login {user_data.server} --token {user_data.token}"
        )

        proc = subprocess.Popen(login_command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        out, err = proc.communicate()
        ret_code = proc.wait()

        if ret_code > 0:
            return bad_request(
                output=out.decode('utf-8') or None,
                errors=err.decode('utf-8') or None
            )

        return request_accepted(
            output=out.decode('utf-8') or None,
        )

