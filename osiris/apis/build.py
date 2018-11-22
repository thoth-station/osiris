# Osiris: Build log aggregator.

"""Namespace: build"""

from flask_restplus import Namespace
from flask_restplus import Resource

from osiris.response import request_accepted


api = Namespace(name='build', description="Namespace for build triggers.")


@api.route('/init/<int:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildInitiated(Resource):
    """Receiver hook for initiated builds."""

    def get(self, build_id):
        """Check whether given build was already initiated."""
        pass

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build initiation hook."""
        pass


@api.route('/start/<int:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildStarted(Resource):
    """Receiver hook for started builds."""

    def get(self, build_id):
        """Check whether given build already started."""
        pass

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build start hook."""
        pass


@api.route('/finish/<int:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildCompleted(Resource):
    """Receiver hook for completed builds."""

    def get(self, build_id):
        """Check whether given build is completed."""
        pass

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build completion hook."""
        pass

