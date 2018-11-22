# Osiris: Build log aggregator.

"""Default API response specifications."""

import typing

from flask import jsonify
from http import HTTPStatus

from osiris import ABOUT


class APIResponse:
    """API response wrapper.

    This decorator can be used to assemble custom payloads
    with default keys common to all responses.
    """

    __BASE_RESPONSE = {
        'name': "Build log aggregator.",
        'version': ABOUT['__version__'],
    }

    def __init__(self, status: HTTPStatus = HTTPStatus.ACCEPTED):
        self._status = status

    def __call__(self, fun: typing.Callable[..., dict] = None):

        def wrapper(*args, **kwargs) -> typing.Tuple[dict, HTTPStatus]:
            response: dict = self.__BASE_RESPONSE.copy()
            response.update({
                'status': f"{self._status}, {self._status.phrase}"
            })

            response.update(fun(*args, **kwargs))

            return jsonify(response), self._status

        return wrapper

    @staticmethod
    def format_status_message(status: HTTPStatus):
        """Return formated status message."""
        return f"{status}, {status.phrase}"


# Syntactic sugar for some of common payloads follows


@APIResponse(HTTPStatus.ACCEPTED)
def request_accepted() -> dict:
    """API response for accepted request."""
    return {}


@APIResponse(HTTPStatus.UNAUTHORIZED)
def request_unauthorized() -> dict:  # pragma: no cover
    """API response for unauthorized request."""
    return {}


@APIResponse(HTTPStatus.FORBIDDEN)
def request_forbidden() -> dict:  # pragma: no cover
    """API response for forbidden request."""
    return {}


@APIResponse(HTTPStatus.BAD_REQUEST)
def bad_request() -> dict:  # pragma: no cover
    """API response for bad request."""
    return {}


@APIResponse(HTTPStatus.OK)
def status_ok() -> dict:  # pragma: no cover
    """API response for status OK.

    NOTE: Used in probes.
    """
    return {}
