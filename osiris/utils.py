# Osiris: Build log aggregator.

"""Utils module."""

import shlex
import subprocess

from http import HTTPStatus


def format_status_message(status: HTTPStatus) -> str:
    """Return formated status message."""
    return f"{status}, {status.phrase}"


def execute_command(command: str) -> tuple:
    """Split safely and execute command as a subprocess."""
    command = shlex.split(command)

    proc = subprocess.Popen(command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    out: bytes
    err: bytes

    out, err = proc.communicate()
    ret_code: int = proc.wait()

    return out, err, ret_code
