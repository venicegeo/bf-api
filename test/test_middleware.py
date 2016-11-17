# Copyright 2016, RadiantBlue Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import logging
import unittest
from unittest.mock import patch, Mock, MagicMock

import flask

from bfapi import piazza
from bfapi.middleware import verify_api_key

API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
AUTH_HEADER = 'Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg=='


@patch('bfapi.piazza.verify_api_key', return_value='test-username')
class VerifyApiKeyFilterTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.middleware')
        self._logger.disabled = True

    def tearDown(self):
        self._logger.disabled = False

    def test_validates_api_key_on_every_request(self, mock: MagicMock):
        endpoints = (
            '/v0/services',
            '/v0/algorithm',
            '/v0/algorithm/test-service-id',
            '/v0/job',
            '/v0/job/test-job-id',
            '/v0/job/by_scene/test-scene-id',
            '/v0/job/by_productline/test-productline-id',
            '/v0/productline',
            '/some/random/unmapped/path',
        )
        for endpoint in endpoints:
            with create_request(endpoint, headers={'Authorization': AUTH_HEADER}):
                verify_api_key()
        self.assertEqual(len(endpoints), mock.call_count)

    def test_allows_public_endpoints_to_pass_through(self, mock: MagicMock):
        endpoints = (
            '/',
            '/login',
            '/v0/scene/event/harvest',
        )
        for endpoint in endpoints:
            with patch('flask.request', path=endpoint, headers={'Authorization': AUTH_HEADER}):
                verify_api_key()
        self.assertEqual(0, mock.call_count)

    def test_attaches_username_to_request(self, _):
        with create_request('/protected', headers={'Authorization': AUTH_HEADER}) as request:
            self.assertFalse(hasattr(request, 'username'))
            verify_api_key()
            self.assertEqual(request.username, 'test-username')

    def test_attaches_api_key_to_request(self, _):
        with create_request('/protected', headers={'Authorization': AUTH_HEADER}) as request:
            self.assertFalse(hasattr(request, 'api_key'))
            verify_api_key()
            self.assertEqual(request.api_key, API_KEY)

    def test_rejects_if_api_key_is_malformed(self, _):
        with create_request('/protected', headers={'Authorization': 'lolwut'}) as request:
            response = verify_api_key()
            self.assertEqual(('Cannot verify malformed API key', 400), response)

    def test_rejects_if_auth_header_is_missing(self, _):
        with create_request('/protected') as request:
            response = verify_api_key()
            self.assertEqual(('Missing authorization header', 400), response)

    def test_rejects_if_api_key_is_expired(self, mock: MagicMock):
        mock.side_effect = piazza.ApiKeyExpired()
        with create_request('/protected', headers={'Authorization': AUTH_HEADER}) as request:
            response = verify_api_key()
            self.assertEqual(('Your Piazza API key has expired', 401), response)

    def test_rejects_when_piazza_throws(self, mock: MagicMock):
        mock.side_effect = piazza.ServerError(500)
        with create_request('/protected', headers={'Authorization': AUTH_HEADER}) as request:
            response = verify_api_key()
            self.assertEqual(('A Piazza error prevents API key verification', 500), response)

    def test_rejects_when_encountering_unexpected_verification_error(self, mock: MagicMock):
        mock.side_effect = FloatingPointError()
        with create_request('/protected', headers={'Authorization': AUTH_HEADER}) as request:
            response = verify_api_key()
            self.assertEqual(('An internal error prevents API key verification', 500), response)


#
# Helpers
#

def create_request(path: str = '/', *, headers: dict = None):
    return patch(
        'flask.request',
        spec=flask.Request,
        path=path,
        headers=headers if headers else {},
    )


#
# Fixtures
#

RESPONSE_SUCCESS = 'RESPONSE_SUCCESS'
