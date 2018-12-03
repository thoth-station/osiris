#!/usr/bin/env python3
# Osiris: Build log aggregator.

"""Flask client."""


from flask import Flask
from flask import jsonify
from flask_restplus import Resource

from osiris.apis import api

from osiris.apis.auth import api as auth_namespace
from osiris.apis.build import api as build_namespace
from osiris.apis.probes import api as probes_namespace

from osiris.exceptions import OCError

from osiris.response import bad_request


app = Flask(__name__)

api.add_namespace(build_namespace)
api.add_namespace(probes_namespace)
api.add_namespace(auth_namespace)

api.init_app(app)


@app.errorhandler(OCError)
def handle_oc_error(error):  # FIXME: The error does not seem to be registered
    """Handle exceptions caused by OC CLI."""
    error_response = jsonify(error.to_dict())

    # TODO: customize response status w.r.t return code
    return bad_request(error=error_response)


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
