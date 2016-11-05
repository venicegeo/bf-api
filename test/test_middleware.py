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

import asyncio
import logging
import unittest
from unittest.mock import patch, Mock, MagicMock

from aiohttp.web import Application, Response, Request

from bfapi import piazza
from bfapi.middleware import create_verify_api_key_filter

API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
AUTH_HEADER = 'Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg=='


class CreateVerifyApiKeyFilterTest(unittest.TestCase):
    def test_returns_api_key_filter(self):
        handler = resolve(create_verify_api_key_filter(create_app(), None))
        self.assertTrue(callable(handler))
        self.assertEqual('verify_api_key', handler.__name__)


@patch('bfapi.piazza.verify_api_key', return_value='test-username')
class VerifyApiKeyFilterTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.middleware')
        self._logger.disabled = True

    def tearDown(self):
        self._logger.disabled = False

    def test_validates_api_key_on_every_request(self, mock: Mock):
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
            simulate_request(create_request(endpoint, headers={'Authorization': AUTH_HEADER}))
        self.assertEqual(len(endpoints), mock.call_count)

    def test_allows_public_endpoints_to_pass_through(self, mock: Mock):
        endpoints = (
            '/',
            '/login',
            '/v0/scene/event/harvest',
        )
        for endpoint in endpoints:
            simulate_request(create_request(endpoint))
        self.assertEqual(0, mock.call_count)

    def test_attaches_username_to_request(self, _):
        request = create_request('/protected', headers={'Authorization': AUTH_HEADER})
        simulate_request(request)
        self.assertTrue(request.__setitem__.called_with('username', 'test-username'))

    def test_attaches_api_key_to_request(self, _):
        request = create_request('/protected', headers={'Authorization': AUTH_HEADER})
        simulate_request(request)
        self.assertTrue(request.__setitem__.called_with('api_key', API_KEY))

    def test_rejects_if_api_key_is_malformed(self, _):
        response = simulate_request(create_request('/protected', headers={'Authorization': 'lolwut'}))
        self.assertEqual(400, response.status)
        self.assertEqual('Cannot verify malformed API key', response.text)

    def test_rejects_if_auth_header_is_missing(self, _):
        response = simulate_request(create_request('/protected'))
        self.assertEqual(400, response.status)
        self.assertEqual('Missing authorization header', response.text)

    def test_rejects_if_api_key_is_expired(self, mock: Mock):
        mock.side_effect = piazza.ApiKeyExpired()
        response = simulate_request(create_request('/protected', headers={'Authorization': AUTH_HEADER}))
        self.assertEqual(401, response.status)
        self.assertEqual('Your Piazza API key has expired', response.text)

    def test_rejects_when_piazza_throws(self, mock: Mock):
        mock.side_effect = piazza.ServerError(500)
        response = simulate_request(create_request('/protected', headers={'Authorization': AUTH_HEADER}))
        self.assertEqual(500, response.status)
        self.assertEqual('A Piazza error prevents API key verification', response.text)

    def test_rejects_when_encountering_unexpected_verification_error(self, mock: Mock):
        mock.side_effect = FloatingPointError()
        response = simulate_request(create_request('/protected', headers={'Authorization': AUTH_HEADER}))
        self.assertEqual(500, response.status)
        self.assertEqual('An internal error prevents API key verification', response.text)

    def test_does_not_hijack_next_handlers_errors_in_protected_path(self, _):
        async def next_handler(_):
            raise ZeroDivisionError()

        with self.assertRaises(ZeroDivisionError):
            simulate_request(create_request('/protected', headers={'Authorization': AUTH_HEADER}), next_handler)

    def test_does_not_hijack_next_handlers_errors_in_public_path(self, _):
        async def next_handler(_):
            raise ZeroDivisionError()

        with self.assertRaises(ZeroDivisionError):
            simulate_request(create_request('/'), next_handler)


#
# Helpers
#

def create_app():
    return Mock(spec=Application)


def create_next_handler():
    async def handler(_):
        return Response(text=RESPONSE_SUCCESS)

    return handler


def create_request(path: str = '/', *, headers: dict = None):
    return MagicMock(
        spec=Request,
        path=path,
        headers=headers if headers else {},
    )


def resolve(future):
    return asyncio.get_event_loop().run_until_complete(future)


def simulate_request(request: Request, next_handler=None) -> Response:
    app = create_app()
    next_handler = next_handler if next_handler else create_next_handler()
    actual_middleware = resolve(create_verify_api_key_filter(app, next_handler))
    return resolve(actual_middleware(request))


#
# Fixtures
#

RESPONSE_SUCCESS = 'RESPONSE_SUCCESS'
