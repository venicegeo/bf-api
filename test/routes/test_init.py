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
from unittest.mock import call, patch, MagicMock

import flask

from bfapi import routes, piazza


@patch('flask.jsonify', side_effect=dict)
@patch('flask.request', path='/')
class HealthCheckTest(unittest.TestCase):
    def test_returns_server_uptime(self, *_):
        response = routes.health_check()
        self.assertIn('uptime', response)
        self.assertIsInstance(response['uptime'], float)


class LoginTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.routes')
        self._logger.disabled = True

        self.mock_create_api_key = self.create_mock('bfapi.piazza.create_api_key', return_value='test-api-key')
        self.mock_jsonify = self.create_mock('flask.jsonify', side_effect=dict)
        self.request = self.create_mock('flask.request', path='/login', headers={})

    def tearDown(self):
        self._logger.disabled = False

    def create_mock(self, target, **kwargs):
        patcher = patch(target, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_rejects_if_missing_auth_header(self):
        self.request.headers = {}
        response = routes.login()
        self.assertEqual(('Authorization header is missing', 401), response)

    def test_passes_correct_credentials_to_piazza(self):
        self.request.headers = {'Authorization': 'test-auth-header'}
        routes.login()
        self.assertEqual(call('test-auth-header'), self.mock_create_api_key.call_args)

    def test_returns_api_key_when_credentials_accepted(self):
        self.request.headers = {'Authorization': 'test-auth-header'}
        response = routes.login()
        self.assertEqual({'api_key': 'test-api-key'}, response)

    def test_rejects_when_credentials_are_malformed(self):
        self.request.headers = {'Authorization': 'test-auth-header'}
        self.mock_create_api_key.side_effect = piazza.MalformedCredentials()
        response = routes.login()
        self.assertEqual(('malformed Piazza credentials', 400), response)

    def test_rejects_when_credentials_are_rejected(self):
        self.request.headers = {'Authorization': 'test-auth-header'}
        self.mock_create_api_key.side_effect = piazza.Unauthorized()
        response = routes.login()
        self.assertEqual(('credentials rejected by Piazza', 401), response)

    def test_rejects_when_piazza_throws(self):
        self.request.headers = {'Authorization': 'test-auth-header'}
        self.mock_create_api_key.side_effect = piazza.ServerError(500)
        response = routes.login()
        self.assertEqual(('A Piazza error prevents login', 500), response)


#
# Helpers
#

def create_request(path: str = '/', *, headers: dict = None):
    return MagicMock(
        'flask.request',
        spec=flask.Request,
        path=path,
        headers=headers if headers else {},
    )
