#!/usr/bin/env python3
# Osiris: Build log aggregator.

"""Flask client."""


from flask import Flask
from flask import jsonify
from flask_restplus import Resource

from osiris.apis import api


app = Flask(__name__)
api.init_app(app)


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
