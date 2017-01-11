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
from unittest.mock import call, patch

import flask

from bfapi.service import users
from bfapi import middleware


class AuthFilterTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.middleware')
        self._logger.disabled = True

        self.mock_authenticate = self.create_mock('bfapi.service.users.authenticate_via_api_key', side_effect=create_user)
        self.request = self.create_mock('flask.request', spec=flask.Request)
        self.session = self.create_mock('flask.session', new={})

    def tearDown(self):
        self._logger.disabled = False

    def create_mock(self, target_name, **kwargs):
        patcher = patch(target_name, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_checks_api_key_for_protected_endpoints(self):
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
            self.request.reset_mock()
            self.request.path = endpoint
            self.request.authorization = {'username': 'test-api-key'}
            middleware.auth_filter()
        self.assertEqual(len(endpoints), self.mock_authenticate.call_count)

    def test_allows_public_endpoints_to_pass_through(self):
        endpoints = (
            '/',
            '/login',
            '/login/geoaxis',
        )
        for endpoint in endpoints:
            self.request.reset_mock()
            self.request.path = endpoint
            middleware.auth_filter()
        self.assertEqual(0, self.mock_authenticate.call_count)

    def test_can_read_api_key_from_session(self):
        self.request.path = '/protected'
        self.request.authorization = None
        self.session['api_key'] = 'test-api-key-from-session'
        self.assertFalse(hasattr(self.request, 'user'))
        middleware.auth_filter()
        self.assertEqual(call('test-api-key-from-session'), self.mock_authenticate.call_args)

    def test_can_read_api_key_from_authorization_header(self):
        self.request.path = '/protected'
        self.request.authorization = {'username': 'test-api-key-from-auth-header'}
        self.assertFalse(hasattr(self.request, 'user'))
        middleware.auth_filter()
        self.assertEqual(call('test-api-key-from-auth-header'), self.mock_authenticate.call_args)

    def test_attaches_user_to_request(self):
        self.request.path = '/protected'
        self.request.authorization = {'username': 'test-api-key'}
        self.assertFalse(hasattr(self.request, 'user'))
        middleware.auth_filter()
        self.assertIsInstance(self.request.user, users.User)
        self.assertEqual('test-user-id', self.request.user.user_id)
        self.assertEqual('test-api-key', self.request.user.api_key)

    def test_rejects_if_api_key_is_missing(self):
        self.request.path = '/protected'
        self.request.authorization = {'username': ''}
        response = middleware.auth_filter()
        self.assertEqual(('Cannot authenticate request: API key is missing', 400), response)

    def test_rejects_if_api_key_is_malformed(self):
        self.mock_authenticate.side_effect = users.MalformedAPIKey()
        self.request.path = '/protected'
        self.request.authorization = {'username': 'lorem'}
        response = middleware.auth_filter()
        self.assertEqual(('Cannot authenticate request: API key is malformed', 400), response)

    def test_rejects_when_api_key_is_not_active(self):
        self.mock_authenticate.side_effect = users.Unauthorized('negative ghost rider')
        self.request.path = '/protected'
        self.request.authorization = {'username': 'test-api-key'}
        response = middleware.auth_filter()
        self.assertEqual(('Unauthorized: negative ghost rider', 401), response)

    def test_rejects_when_encountering_unexpected_verification_error(self):
        self.mock_authenticate.side_effect = users.Error('random error of known type')
        self.request.path = '/protected'
        self.request.authorization = {'username': 'test-api-key'}
        response = middleware.auth_filter()
        self.assertEqual(('Cannot authenticate request: an internal error prevents API key verification', 500), response)


class CSRFFilterTest(unittest.TestCase):
    maxDiff = 4096

    def setUp(self):
        self._logger = logging.getLogger('bfapi.middleware')
        self._logger.disabled = True

        self.request = self.create_mock('flask.request', spec=flask.Request, headers={}, referrer=None, remote_addr='1.2.3.4')

    def tearDown(self):
        self._logger.disabled = False

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

    def test_allows_non_cors_requests(self):
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
            self.request.reset_mock()
            self.request.path = endpoint
            self.request.headers['Origin'] = ''
            self.request.referrer = None
            response = middleware.csrf_filter()
            self.assertIsNone(response)

    def test_allows_cors_requests_from_authorized_origins(self):
        origins = middleware.AUTHORIZED_ORIGINS
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            response = middleware.csrf_filter()
            self.assertIsNone(response)

    def test_rejects_cors_requests_from_unknown_origins(self):
        origins = (
            'http://beachfront.{}'.format(middleware.DOMAIN),  # Not HTTPS
            'http://bf-swagger.{}'.format(middleware.DOMAIN),  # Not HTTPS
            'http://instaspotifriendspacebooksterifygram.com',
            'https://beachfront.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
            'https://bf-api.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
            'https://bf-swagger.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
        )
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            response = middleware.csrf_filter()
            self.assertEqual(('Access Denied: CORS request validation failed', 403), response)

    def test_rejects_cors_requests_suspected_as_spoofed(self):
        origins = (
            'http://beachfront.{}'.format(middleware.DOMAIN),  # Not HTTPS
            'http://bf-swagger.{}'.format(middleware.DOMAIN),  # Not HTTPS
            'http://instaspotifriendspacebooksterifygram.com',
            'https://beachfront.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
            'https://bf-api.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
            'https://bf-swagger.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
        )
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = None
            self.request.referrer = origin
            response = middleware.csrf_filter()
            self.assertEqual(('Access Denied: CORS request validation failed', 403), response)

    def test_logs_rejection_of_cors_requests_from_unknown_origin(self):
        logstream = self.create_logstream()
        origins = (
            'http://beachfront.{}'.format(middleware.DOMAIN),  # Not HTTPS
            'http://bf-swagger.{}'.format(middleware.DOMAIN),  # Not HTTPS
            'http://instaspotifriendspacebooksterifygram.com',
            'https://beachfront.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
            'https://bf-api.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
            'https://bf-swagger.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
        )
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            middleware.csrf_filter()
        self.assertEqual([
            'WARNING - Possible CSRF attempt from unknown origin: endpoint=`/protected` origin=`http://beachfront.localhost` referrer=`None` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt from unknown origin: endpoint=`/protected` origin=`http://bf-swagger.localhost` referrer=`None` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt from unknown origin: endpoint=`/protected` origin=`http://instaspotifriendspacebooksterifygram.com` referrer=`None` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt from unknown origin: endpoint=`/protected` origin=`https://beachfront.localhost.totallynotaphishingattempt.com` referrer=`None` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt from unknown origin: endpoint=`/protected` origin=`https://bf-api.localhost.totallynotaphishingattempt.com` referrer=`None` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt from unknown origin: endpoint=`/protected` origin=`https://bf-swagger.localhost.totallynotaphishingattempt.com` referrer=`None` ip=`1.2.3.4`',
        ], logstream.getvalue().splitlines())

    def test_logs_rejection_of_cors_requests_suspected_of_script_tag_spoofing(self):
        logstream = self.create_logstream()
        origins = (
            'http://beachfront.{}'.format(middleware.DOMAIN),  # Not HTTPS
            'http://bf-swagger.{}'.format(middleware.DOMAIN),  # Not HTTPS
            'http://instaspotifriendspacebooksterifygram.com',
            'https://beachfront.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
            'https://bf-api.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
            'https://bf-swagger.{}.totallynotaphishingattempt.com'.format(middleware.DOMAIN),
        )
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = None
            self.request.referrer = origin
            middleware.csrf_filter()
        self.assertEqual([
            'WARNING - Possible CSRF attempt via <script/> tag: endpoint=`/protected` origin=`None` referrer=`http://beachfront.localhost` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt via <script/> tag: endpoint=`/protected` origin=`None` referrer=`http://bf-swagger.localhost` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt via <script/> tag: endpoint=`/protected` origin=`None` referrer=`http://instaspotifriendspacebooksterifygram.com` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt via <script/> tag: endpoint=`/protected` origin=`None` referrer=`https://beachfront.localhost.totallynotaphishingattempt.com` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt via <script/> tag: endpoint=`/protected` origin=`None` referrer=`https://bf-api.localhost.totallynotaphishingattempt.com` ip=`1.2.3.4`',
            'WARNING - Possible CSRF attempt via <script/> tag: endpoint=`/protected` origin=`None` referrer=`https://bf-swagger.localhost.totallynotaphishingattempt.com` ip=`1.2.3.4`',
        ], logstream.getvalue().splitlines())


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

def create_user(api_key: str) -> users.User:
    return users.User(
        user_id='test-user-id',
        api_key=api_key,
        name='test-name',
    )
