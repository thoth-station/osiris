"""Tests for response module."""

from http import HTTPStatus
from unittest import TestCase
from unittest.mock import patch

from osiris.response import APIResponse
from osiris.response import request_accepted
from osiris.utils import format_status_message


def patch_jsonify(response_dict: dict) -> dict:
    """Patch `flask.jsonify` function to return identity."""

    return response_dict


class TestResponse(TestCase):

    @patch('osiris.response.jsonify', patch_jsonify)
    def test_request_accepted(self):

        expected_status = HTTPStatus.ACCEPTED
        response, status = request_accepted()

        self.assertIsInstance(response, dict)

        self.assertIsInstance(
            response.pop('name'), str
        )
        self.assertIsInstance(
            response.pop('version'), str
        )
        self.assertEqual(
            response.pop('status')['code'],
            expected_status.value
        )
        self.assertFalse(response)

        self.assertEqual(status, expected_status)
