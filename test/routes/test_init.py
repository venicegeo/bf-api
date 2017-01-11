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
from unittest.mock import call, patch

from bfapi import routes
from bfapi.service import users


@patch('flask.jsonify', side_effect=dict)
@patch('flask.request', path='/')
class HealthCheckTest(unittest.TestCase):
    def test_returns_server_uptime(self, *_):
        response = routes.health_check()
        self.assertIn('uptime', response)
        self.assertIsInstance(response['uptime'], float)


@patch('bfapi.routes.GEOAXIS', new='geoaxis.localhost')
@patch('bfapi.routes.GEOAXIS_CLIENT_ID', new='test-geoaxis-client-id')
class LoginStartCheckTest(unittest.TestCase):
    maxDiff = 4096

    def test_redirects_to_geoaxis_oauth_authorization(self):
        response = routes.login_start()
        self.assertEqual(
            'https://geoaxis.localhost/ms_oauth/oauth2/endpoints/oauthservice/authorize' +
            '?client_id=test-geoaxis-client-id' +
            '&redirect_uri=https%3A%2F%2Fbf-api.localhost%2Flogin' +
            '&response_type=code' +
            '&scope=UserProfile.me',
            response.location,
        )


class LoginTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.routes')
        self._logger.disabled = True

        self.mock_authenticate = self.create_mock('bfapi.service.users.authenticate_via_geoaxis', return_value=None)
        self.mock_redirect = self.create_mock('flask.redirect')
        self.request = self.create_mock('flask.request', path='/login', args={})
        self.session = self.create_mock('flask.session', new={})

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
        self.mock_authenticate.return_value = create_user()
        self.request.args = {'code': 'test-auth-code'}
        routes.login()
        self.assertEqual(call('test-auth-code'), self.mock_authenticate.call_args)

    def test_attaches_api_key_to_session_on_auth_success(self):
        self.mock_authenticate.return_value = create_user()
        self.request.args = {'code': 'test-auth-code'}
        routes.login()
        self.assertEqual({'api_key': 'test-api-key'}, self.session)

    def test_redirects_to_ui_url_on_auth_success(self):
        self.mock_authenticate.return_value = create_user()
        self.request.args = {'code': 'test-auth-code'}
        response = routes.login()
        self.assertEqual(self.mock_redirect.return_value, response)
        self.assertEqual(call('https://beachfront.localhost?logged_in=true'), self.mock_redirect.call_args)

    def test_rejects_when_credentials_are_rejected(self):
        self.mock_authenticate.side_effect = users.Unauthorized('test-error-message')
        self.request.args = {'code': 'test-auth-code'}
        response = routes.login()
        self.assertEqual(('Unauthorized: test-error-message', 401), response)

    def test_rejects_when_users_service_throws(self):
        self.mock_authenticate.side_effect = users.Error('oh noes')
        self.request.args = {'code': 'test-auth-code'}
        response = routes.login()
        self.assertEqual(('Cannot log in: an internal error prevents authentication', 500), response)


#
# Helpers
#

def create_user():
    return users.User(
        user_id='CN=test-commonname,O=test-org,C=test-country',
        api_key='test-api-key',
        name='test-name',
    )
