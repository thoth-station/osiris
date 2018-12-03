# Osiris: Build log aggregator.

"""Default API response specifications."""

import typing

from http import HTTPStatus
from osiris.schema.base import Base, BaseSchema


__schema__ = BaseSchema()


def status(http_status: HTTPStatus):
    """API response wrapper.

    This decorator can be used to assemble custom payloads
    with default keys common to all responses.
    """

    def wrapper(fun: typing.Callable[..., dict] = None):

        def inner(*args, **kwargs) -> typing.Tuple[dict, HTTPStatus]:
            base = Base(http_status)

            response = __schema__.dump(base)
            response.data.update(fun(*args, **kwargs))

            return response.data, http_status.value

        return inner

    return wrapper

# Syntactic sugar for some of common payloads follows


@status(HTTPStatus.ACCEPTED)
def request_accepted(**kwargs) -> dict:
    """API response for accepted request.

    Request accepted, processing continues off-line.
    """
    return kwargs


@status(HTTPStatus.CREATED)
def request_created(**kwargs) -> dict:
    """API response for created request.

    Document created, URL follows.
    """
    return kwargs


@status(HTTPStatus.UNAUTHORIZED)
def request_unauthorized(**kwargs) -> dict:  # pragma: no cover
    """API response for unauthorized request.

    No permission -- see authorization schemes.
    """
    return kwargs


@status(HTTPStatus.FORBIDDEN)
def request_forbidden(**kwargs) -> dict:  # pragma: no cover
    """API response for forbidden request.

    Request forbidden -- authorization will not help.
    """
    return kwargs


@status(HTTPStatus.BAD_REQUEST)
def bad_request(**kwargs) -> dict:  # pragma: no cover
    """API response for bad request.

    Bad request syntax or unsupported method.
    """
    return kwargs


@status(HTTPStatus.OK)
def request_ok(**kwargs) -> dict:  # pragma: no cover
    """API response for status OK.

    Request fulfilled, document follows.
    """
    return kwargs
