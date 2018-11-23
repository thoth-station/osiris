# Osiris: Build log aggregator.

"""Namespace: build"""

from flask_restplus import Namespace
from flask_restplus import Resource

from osiris.model import build_status_model
from osiris.model import build_info_model
from osiris.response import status_ok
from osiris.response import request_created
from osiris.response import request_accepted


api = Namespace(name='build', description="Namespace for build triggers.")


@api.route('/status/<int:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildStatus(Resource):
    """Build status endpoint."""

    # noinspection PyMethodMayBeStatic
    @api.marshal_with(build_status_model)
    def get(self, build_id):
        """Return status of the given build."""
        pass
        return status_ok()


@api.route('/info/<int:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildInfo(Resource):
    """Build information endpoint."""

    # noinspection PyMethodMayBeStatic
    @api.marshal_with(build_info_model)
    def get(self, build_id):
        """Return complete information stored about given build."""
        pass
        return status_ok()


@api.route('/logs/<int:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildLog(Resource):
    """Build log endpoint."""

    # noinspection PyMethodMayBeStatic
    # @api.marshal_with(build_logs_model)
    def get(self, build_id):
        """Return logs stored by the given build."""
        pass
        return status_ok()


@api.route('/init/<int:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildInitiated(Resource):
    """Receiver hook for initiated builds."""

    # noinspection PyMethodMayBeStatic
    @api.marshal_with(build_status_model)
    def put(self, build_id):  # pragma: no cover
        """Trigger build initiation hook."""
        return request_accepted()


@api.route('/start/<int:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildStarted(Resource):
    """Receiver hook for started builds."""

    # noinspection PyMethodMayBeStatic
    @api.marshal_with(build_status_model)
    def put(self, build_id):  # pragma: no cover
        """Trigger build start hook."""
        return request_accepted()


@api.route('/finish/<int:build_id>')
@api.param('build_id', 'Unique build identification.')
class BuildCompleted(Resource):
    """Receiver hook for completed builds.

    When the build is marked completed and this endpoint
    is triggered, the aggregator will automatically gather
    logs for the given build.
    """

    # noinspection PyMethodMayBeStatic
    @api.marshal_with(build_status_model)
    def get(self, build_id):
        """Check whether given build is completed."""
        return status_ok()

    # noinspection PyMethodMayBeStatic
    def put(self, build_id):  # pragma: no cover
        """Trigger build completion hook."""
        return request_accepted()
