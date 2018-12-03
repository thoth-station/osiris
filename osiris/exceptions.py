# Osiris: Build log aggregator.

"""API exceptions."""

from werkzeug.exceptions import InternalServerError


class OCError(InternalServerError):
    """Exception raised on OC CLI failure."""

    def __init__(self, ret_code: int, payload=None):
        super(InternalServerError, self).__init__()

        self.ret_code = ret_code
        self.message = f"OC CLI returned non-zero value: {ret_code}"
        self.payload = payload

    def to_dict(self) -> dict:
        """Dump exception info into dict."""
        rv = {
            'error_code': self.ret_code,
            'error_message': self.message,
            'error_payload': self.payload or {},
        }

        return rv
