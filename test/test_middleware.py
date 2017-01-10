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

import io
import logging
import unittest
from unittest.mock import patch, Mock

import flask

from bfapi.service import users
from bfapi import middleware

API_KEY = 'aaaaaaaabbbbccccddddeeeeeeeeeeee'


@patch('bfapi.service.users.authenticate_via_api_key', side_effect=lambda _: create_user())
class VerifyApiKeyFilterTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.middleware')
        self._logger.disabled = True

    def tearDown(self):
        self._logger.disabled = False

    def test_checks_api_key_on_every_request(self, mock: MagicMock):
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
            with create_request(endpoint, api_key=API_KEY):
                verify_api_key()
        self.assertEqual(len(endpoints), mock.call_count)

    def test_allows_public_endpoints_to_pass_through(self, mock: MagicMock):
        endpoints = (
            '/',
            '/login',
        )
        for endpoint in endpoints:
            with patch('flask.request', path=endpoint, api_key=API_KEY):
                verify_api_key()
        self.assertEqual(0, mock.call_count)

    def test_attaches_user_to_request(self, _):
        with create_request('/protected', api_key=API_KEY) as request:
            self.assertFalse(hasattr(request, 'username'))
            verify_api_key()
            self.assertIsInstance(request.user, users.User)
            self.assertEqual('test-user-id', request.user.user_id)
            self.assertEqual(API_KEY, request.user.api_key)

    def test_rejects_if_api_key_is_missing(self, _):
        with create_request('/protected', api_key=''):
            response = verify_api_key()
            self.assertEqual(('Missing API key', 400), response)

    def test_rejects_when_geoaxis_throws(self, mock: MagicMock):
        mock.side_effect = users.GeoaxisError(500)
        with create_request('/protected', api_key=API_KEY):
            response = verify_api_key()
            self.assertEqual(('Cannot authenticate request: an internal error prevents API key verification', 500), response)

    def test_rejects_when_geoaxis_is_down(self, mock: MagicMock):
        mock.side_effect = users.GeoaxisUnreachable()
        with create_request('/protected', api_key=API_KEY):
            response = verify_api_key()
            self.assertEqual(('Cannot authenticate request: GeoAxis cannot be reached', 503), response)

    def test_rejects_when_encountering_unexpected_verification_error(self, mock: MagicMock):
        mock.side_effect = users.Error('random error of known type')
        with create_request('/protected', api_key=API_KEY):
            response = verify_api_key()
            self.assertEqual(('Cannot authenticate request: an internal error prevents API key verification', 500), response)



class HTTPSFilterTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.middleware')
        self._logger.disabled = True

        self.request = self.create_mock('flask.request', path='/test-path', referrer='http://test-referrer')

    def create_mock(self, target_name, **kwargs):
        patcher = patch(target_name, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def create_logstream(self) -> io.StringIO:
        def cleanup():
            self._logger.propagate = True

        self._logger.propagate = False
        self._logger.disabled = False
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self._logger.addHandler(handler)
        self.addCleanup(cleanup)
        return stream

    def tearDown(self):
        self._logger.disabled = False

    def test_rejects_non_https_requests(self):
        self.request.is_secure = False
        response = middleware.https_filter()
        self.assertEqual(('Access Denied: Please retry with HTTPS', 403), response)

    def test_logs_rejection(self):
        self.request.is_secure = False
        logstream = self.create_logstream()
        middleware.https_filter()
        self.assertEqual([
            'WARNING - Rejecting non-HTTPS request: endpoint=`/test-path` referrer=`http://test-referrer`',
        ], logstream.getvalue().splitlines())


#
# Helpers
#

def create_user() -> users.User:
    return users.User(
        user_id='test-user-id',
        api_key=API_KEY,
        name='test-name',
    )
