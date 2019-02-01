# Osiris: Build log aggregator.

"""API exceptions."""

from werkzeug.exceptions import InternalServerError
from werkzeug.exceptions import Unauthorized


class OCError(InternalServerError):
    """Exception raised on generic OC CLI failure."""

    def __init__(self, ret_code: int, payload=None, response=None):
        """Initialize OCError class."""
        super(InternalServerError, self).__init__()

        self.ret_code = ret_code
        self.message = f"OC CLI returned non-zero value: {ret_code}"
        self.payload = payload

        self.response = response

    def to_dict(self) -> dict:
        """Dump exception info into dict."""
        rv = {
            'error_code': self.ret_code,
            'error_message': self.message,
            'error_payload': self.payload or {},
        }

        return rv


class OCAuthenticationError(Unauthorized):
    """Exception raised on OC CLI failure."""

    def __init__(self, payload=None, response=None):
        """Initialize OCAuthenticationError class."""
        super(Unauthorized, self).__init__()

        self.message = f"Client has not been authenticated"
        self.payload = payload

        self.response = response

    def to_dict(self) -> dict:
        """Dump exception info into dict."""
        rv = {
            'error_code': self.code,
            'error_description': self.description,
            'error_message': self.message,
            'error_payload': self.payload or {},
        }

        return rv
