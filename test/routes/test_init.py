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

from bfapi import routes
from bfapi.service import users


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

        self.mock_authenticate = self.create_mock('bfapi.service.users.authenticate_via_geoaxis', return_value=create_user())
        self.mock_jsonify = self.create_mock('flask.jsonify', side_effect=dict)
        self.request = self.create_mock('flask.request', path='/login', args={})

    def tearDown(self):
        self._logger.disabled = False

    def create_mock(self, target, **kwargs):
        patcher = patch(target, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_rejects_when_auth_code_is_missing(self):
        self.request.args = {}
        response = routes.login()
        self.assertEqual(('Cannot log in: invalid "code" query parameter', 400), response)

    def test_rejects_when_auth_code_is_blank(self):
        self.request.args = {'code': ''}
        response = routes.login()
        self.assertEqual(('Cannot log in: invalid "code" query parameter', 400), response)

    def test_passes_correct_auth_code_to_users_service(self):
        self.request.args = {'code': 'test-auth-code'}
        routes.login()
        self.assertEqual(call('test-auth-code'), self.mock_authenticate.call_args)

    def test_returns_api_key_when_credentials_accepted(self):
        self.request.args = {'code': 'test-auth-code'}
        response = routes.login()
        self.assertEqual({'api_key': 'test-api-key'}, response)

    def test_rejects_when_credentials_are_rejected(self):
        self.request.args = {'code': 'test-auth-code'}
        self.mock_authenticate.side_effect = users.Unauthorized('test-error-message')
        response = routes.login()
        self.assertEqual(('Unauthorized: test-error-message', 401), response)

    def test_rejects_when_users_service_throws(self):
        self.request.args = {'code': 'test-auth-code'}
        self.mock_authenticate.side_effect = users.Error('oh noes')
        response = routes.login()
        self.assertEqual(('Cannot log in: an internal error prevents authentication', 500), response)


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

def create_user():
    return users.User(
        user_id='CN=test-commonname,O=test-org,C=test-country',
        api_key='test-api-key',
        name='test-name',
    )
