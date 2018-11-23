# Osiris: Build log aggregator.

"""Utils module."""

from http import HTTPStatus


def format_status_message(status: HTTPStatus):
    """Return formated status message."""
    return f"{status}, {status.phrase}"
