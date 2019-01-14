#!/usr/bin/env python3
# Osiris: Build log aggregator.

"""Flask client."""

import os
import sys
import logging

from http import HTTPStatus
from typing import Union

from flask import Flask
from flask import jsonify
from flask import request
from flask_restplus import Resource

from marshmallow import ValidationError

from osiris import __name__ as __APP_NAME__
from osiris.apis import api

from osiris.apis.auth import api as auth_namespace
from osiris.apis.build import api as build_namespace
from osiris.apis.probes import api as probes_namespace

from osiris.exceptions import OCError
from osiris.exceptions import OCAuthenticationError

from osiris.response import bad_request

app = Flask(__name__)

app.logger.setLevel(
    getattr(logging, os.getenv('LOGGING_LEVEL', 'INFO'), logging.INFO)
)

api.add_namespace(build_namespace)
api.add_namespace(probes_namespace)
api.add_namespace(auth_namespace)

api.init_app(app)


@app.after_request
def log_request(response):

    prefix = f"[{__APP_NAME__.upper()}]"

    app.logger.debug(f"{prefix} Request received.")

    addr = request.headers.get('X-Forwarded-For', request.remote_addr)
    host = request.host.split(':', 1)[0]

    log_params = [
        ('method', request.method.upper()),
        ('path', request.path),
        ('remote_addr', addr),
        ('host', host),
        ('status', response.status_code),
        ('params', request.args),
        ('data', request.json),
    ]

    log_msg = "  ".join([f"{param}={value}" for param, value in log_params])

    app.logger.debug(f"{prefix} {log_msg}")

    return response


def log_build_request(response):
    """Log build requests"""

    prefix = "[BUILD]"

    app.logger.info(f"{prefix} Request accepted.")
    app.logger.info(f"{prefix} Body: {request.json}.")

    return response


app.after_request_funcs['build'] = log_build_request


@app.errorhandler(OCError)
@app.errorhandler(OCAuthenticationError)
def handle_oc_error(
        error: Union[OCError, OCAuthenticationError]):
    """Handle exceptions caused by OC CLI."""
    error_dct = error.to_dict()
    error_response = error.response or bad_request

    return jsonify(error_response(errors=error_dct)), error.code


@app.errorhandler(ValidationError)
def handle_schema_validation_error(error: ValidationError):
    """Handle exceptions caused by OC CLI."""
    error_dct = error.messages

    return jsonify(bad_request(errors=error_dct)), HTTPStatus.BAD_REQUEST


# Namespace: default
# ---

@api.route('/api', '/schema')
class APISchema(Resource):
    """Swagger specification for this API."""

    # noinspection PyMethodMayBeStatic
    def get(self):  # pragma: no cover
        return jsonify(api.__schema__)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)  # FIXME: turn off debug mode, set port
