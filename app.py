#!/usr/bin/env python3
# Osiris: Build log aggregator.

"""Flask client."""


from flask import Flask
from flask import jsonify
from flask_restplus import Api
from flask_restplus import Resource

from osiris import __about__


ABOUT = dict()

with open(__about__.__file__) as f:
    exec(f.read(), ABOUT)


app = Flask(__name__)
api = Api(app,
          version=ABOUT['__version__'],
          title=ABOUT['__title__'],
          description=ABOUT['__summary__'])


ns_check = api.namespace(name='check',
                         description="Namespace for API health checks.")


@ns_check.route('/liveness')
class Liveness(Resource):
    """Health check."""

    # noinspection PyMethodMayBeStatic
    def get(self):  # pragma: no cover
        return jsonify({
            'name': "Build log aggregator.",
            'version': ABOUT['__version__'],
            'status': 'Status OK'
        })


@ns_check.route('/readiness')
class Readiness(Resource):
    """Readiness check.

    Checks Ceph storage availability.
    """

    # noinspection PyMethodMayBeStatic
    def get(self):
        return jsonify({
            'name': "Build log aggregator.",
            'version': ABOUT['__version__'],
            'status': 'Status READY'  # TODO: check Ceph
        })


@api.route('/api', '/schema')
class APISchema(Resource):
    """Swagger specification for this API."""

    # noinspection PyMethodMayBeStatic
    def get(self):  # pragma: no cover
        return jsonify(api.__schema__)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)  # FIXME: turn off debug mode, set port
