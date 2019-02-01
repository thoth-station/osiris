#!/usr/bin/env python3
# Osiris: Build log aggregator.

"""Flask client."""

import logging
import traceback

from datetime import datetime

from typing import Union

from flask import Flask
from flask import jsonify
from flask import request
from flask_restplus import Resource

from marshmallow import ValidationError

from osiris import __name__ as __APP_NAME__
from osiris import DEFAULT_LOG_LEVEL
from osiris import get_oc_client

from osiris.apis import api

from osiris.exceptions import OCError
from osiris.exceptions import OCAuthenticationError

from osiris.response import bad_request

from thoth.common.openshift import OpenShift

from werkzeug.exceptions import InternalServerError


app = Flask(__name__)

app.logger.setLevel(
    level=getattr(logging, DEFAULT_LOG_LEVEL, logging.INFO)
)

api.init_app(app)


@app.before_first_request
def check_configuration():
    """Check client configuration."""
    client: OpenShift = get_oc_client()

    prefix = f"[{__APP_NAME__.upper()}]"

    if client.in_cluster:
        app.logger.info(f"{prefix} Running in Kubernetes cluster.")

    app.logger.debug(f"{prefix} OpenShift Client Configuration: %s",
                     client.ocp_client.configuration.__dict__)


@app.after_request
def log_request(response):
    """Log request details after each request."""
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
    app.logger.debug(f"{prefix} Response: {response.json}")

    return response


# Error handlers
# ---

@app.errorhandler(OCError)
@app.errorhandler(OCAuthenticationError)
def handle_oc_error(
        error: Union[OCError, OCAuthenticationError]):
    """Handle exceptions caused by OC CLI."""
    error_dct = error.to_dict()
    error_response = error.response or bad_request

    app.logger.error(traceback.format_exc())

    resp, code = error_response(errors=error_dct)
    return jsonify(resp), code


@app.errorhandler(ValidationError)
def handle_schema_validation_error(error: ValidationError):
    """Handle exceptions caused by OC CLI."""
    error_dct = error.messages

    app.logger.error(traceback.format_exc())

    resp, code = bad_request(errors=error_dct)
    return jsonify(resp), code


@app.errorhandler(InternalServerError)
def handle_internal_server_error(exc):
    """Handle internal server errors."""
    # Provide some additional information so we can easily find exceptions in logs (time and exception type).
    # Later we should remove exception type (for security reasons).
    app.logger.error(traceback.format_exc())

    return jsonify({
        "message": "Internal server error occurred, please contact administrator with provided details.",
        "details": {"type": exc.__class__.__name__, "datetime": datetime.utcnow().isoformat()},
    }), 500


@app.errorhandler(Exception)
def handle_unknown_exception(exc):
    """Handle internal server errors."""
    # Provide some additional information so we can easily find exceptions in logs (time and exception type).
    # Later we should remove exception type (for security reasons).
    app.logger.error(traceback.format_exc())

    return jsonify({
        "message": "Unknown exception occurred",
        "details": {"type": exc.__class__.__name__,
                    "traceback": traceback.format_exc(),
                    "datetime": datetime.utcnow().isoformat()},
    }), 500


# Namespace: default
# ---

@api.route('/api', '/schema')
class APISchema(Resource):
    """Swagger specification for this API."""

    # noinspection PyMethodMayBeStatic
    def get(self):  # pragma: no cover
        """Return complete API sChema specification."""
        return jsonify(api.__schema__)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)  # FIXME: turn off debug mode, set port
