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
import json
import unittest
from unittest.mock import call, patch, MagicMock

from aiohttp import Request, Response

from bfapi import routes, piazza


class HealthCheckTest(unittest.TestCase):
    def setUp(self):
        self.conn = unittest.mock.Mock()

    def test_returns_server_uptime(self):
        request = create_request()
        response = simulate_request(request, routes.health_check)
        self.assertIn('uptime', json.loads(response.body.decode()))
        self.assertIsInstance(json.loads(response.body.decode())['uptime'], float)


@patch('bfapi.piazza.create_api_key', return_value='test-api-key')
class LoginTest(unittest.TestCase):
    def setUp(self):
        self.conn = unittest.mock.Mock()

    def test_rejects_if_missing_auth_header(self, _):
        request = create_request()
        response = simulate_request(request, routes.login)
        self.assertEqual(401, response.status)
        self.assertEqual('Authorization header is missing', response.body.decode())

    def test_passes_correct_credentials_to_piazza(self, mock: MagicMock):
        request = create_request(headers={'Authorization': 'test-auth-header'})
        simulate_request(request, routes.login)
        self.assertEqual(call('test-auth-header'), mock.call_args)

    def test_returns_api_key_when_credentials_accepted(self, mock: MagicMock):
        request = create_request(headers={'Authorization': 'test-auth-header'})
        response = simulate_request(request, routes.login)
        self.assertEqual(200, response.status)
        self.assertEqual({'api_key': 'test-api-key'}, json.loads(response.body.decode()))

    def test_rejects_when_credentials_are_malformed(self, mock: MagicMock):
        mock.side_effect = piazza.MalformedCredentials()
        request = create_request(headers={'Authorization': 'test-auth-header'})
        response = simulate_request(request, routes.login)
        self.assertEqual(400, response.status)
        self.assertEqual('malformed Piazza credentials', response.body.decode())

    def test_rejects_when_credentials_are_rejected(self, mock: MagicMock):
        mock.side_effect = piazza.Unauthorized()
        request = create_request()
        response = simulate_request(request, routes.login)
        self.assertEqual(401, response.status)
        self.assertEqual('Authorization header is missing', response.body.decode())

    def test_rejects_when_piazza_throws(self, mock: MagicMock):
        mock.side_effect = piazza.ServerError(500)
        request = create_request(headers={'Authorization': 'test-auth-header'})
        response = simulate_request(request, routes.login)
        self.assertEqual(500, response.status)
        self.assertEqual('A Piazza error prevents login', response.body.decode())


#
# Helpers
#

def create_request(path: str = '/', *, headers: dict = None) -> MagicMock:
    return MagicMock(
        spec=Request,
        path=path,
        headers=headers if headers else {},
    )


def resolve(future):
    return asyncio.get_event_loop().run_until_complete(future)


def simulate_request(request: Request, handler) -> Response:
    return resolve(handler(request))
