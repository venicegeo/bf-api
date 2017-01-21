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

AUTHORIZED_ORIGINS = (
    'https://beachfront.geointservices.io',
    'https://beachfront.dev.geointservices.io',
    'https://beachfront.int.geointservices.io',
    'https://beachfront.stage.geointservices.io',
    'https://beachfront.arbitrary.subdomain.geointservices.io',
    'https://bf-swagger.geointservices.io',
    'https://bf-swagger.dev.geointservices.io',
    'https://bf-swagger.int.geointservices.io',
    'https://bf-swagger.stage.geointservices.io',
    'https://bf-swagger.arbitrary.subdomain.geointservices.io',
    'https://localhost:8080',
)

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
        self.assertEqual(('Cannot authenticate request: API key is missing', 401), response)

    def test_rejects_if_api_key_is_malformed(self):
        self.mock_authenticate.side_effect = users.MalformedAPIKey()
        self.request.path = '/protected'
        self.request.authorization = {'username': 'lorem'}
        response = middleware.auth_filter()
        self.assertEqual(('Cannot authenticate request: API key is malformed', 401), response)

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

        self.request = self.create_mock('flask.request',
                                        spec=flask.Request,
                                        headers={},
                                        method='GET',
                                        referrer=None,
                                        remote_addr='1.2.3.4',
                                        is_xhr=False)

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
            self.request.headers['Origin'] = None
            self.request.referrer = None
            self.request.is_xhr = False
            response = middleware.csrf_filter()
            self.assertIsNone(response)

    def test_allows_cors_requests_from_authorized_origins(self):
        origins = AUTHORIZED_ORIGINS
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            self.request.is_xhr = True
            response = middleware.csrf_filter()
            self.assertIsNone(response)

    def test_allows_cors_preflights_from_authorized_origins(self):
        origins = AUTHORIZED_ORIGINS
        for origin in origins:
            self.request.reset_mock()
            self.request.method = 'OPTIONS'
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            self.request.headers['Access-Control-Request-Headers'] = 'Content-Type,X-Requested-With'
            self.request.is_xhr = False
            response = middleware.csrf_filter()
            self.assertIsNone(response)

    def test_rejects_cors_requests_from_unknown_origins(self):
        origins = (
            'http://beachfront.geointservices.io',  # Not HTTPS
            'http://bf-swagger.geointservices.io',  # Not HTTPS
            'http://instaspotifriendspacebooksterifygram.com',
            'https://beachfront.geointservices.io.totallynotaphishingattempt.com',
            'https://bf-swagger.geointservices.io.totallynotaphishingattempt.com',
        )
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            self.request.is_xhr = True
            response = middleware.csrf_filter()
            self.assertEqual(('Access Denied: CORS request validation failed', 403), response)

    def test_rejects_cors_preflights_from_unknown_origins(self):
        origins = (
            'http://beachfront.geointservices.io',  # Not HTTPS
            'http://bf-swagger.geointservices.io',  # Not HTTPS
            'http://instaspotifriendspacebooksterifygram.com',
            'https://beachfront.geointservices.io.totallynotaphishingattempt.com',
            'https://bf-swagger.geointservices.io.totallynotaphishingattempt.com',
        )
        for origin in origins:
            self.request.reset_mock()
            self.request.method = 'OPTIONS'
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            self.request.headers['Access-Control-Request-Headers'] = 'Content-Type,X-Requested-With'
            self.request.is_xhr = True
            response = middleware.csrf_filter()
            self.assertEqual(('Access Denied: CORS request validation failed', 403), response)

    def test_rejects_cors_requests_that_look_spoofed(self):
        """
        Background:

        If `Origin` is empty and `Referrer` is not, more than likely the call
        came from an <img/> or <script/> tag, neither of which are legit uses
        """
        origins = AUTHORIZED_ORIGINS
        for origin in origins:
            self.request.path = '/protected'
            self.request.headers['Origin'] = None
            self.request.referrer = origin
            response = middleware.csrf_filter()
            self.assertEqual(('Access Denied: CORS request validation failed', 403), response)

    def test_rejects_cors_requests_not_marked_as_xhr(self):
        origins = AUTHORIZED_ORIGINS
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            self.request.referrer = origin
            self.request.is_xhr = False
            response = middleware.csrf_filter()
            self.assertEqual(('Access Denied: CORS request validation failed', 403), response)

    def test_logs_rejection_of_cors_requests_from_unknown_origin(self):
        logstream = self.create_logstream()
        origins = (
            'http://beachfront.geointservices.io',  # Not HTTPS
            'http://bf-swagger.geointservices.io',  # Not HTTPS
            'http://instaspotifriendspacebooksterifygram.com',
            'https://beachfront.geointservices.io.totallynotaphishingattempt.com',
            'https://bf-swagger.geointservices.io.totallynotaphishingattempt.com',
        )
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            self.request.is_xhr = True
            middleware.csrf_filter()
        self.assertEqual([
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`http://beachfront.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`http://bf-swagger.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`http://instaspotifriendspacebooksterifygram.com` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://beachfront.geointservices.io.totallynotaphishingattempt.com` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://bf-swagger.geointservices.io.totallynotaphishingattempt.com` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
        ], logstream.getvalue().splitlines())

    def test_logs_rejection_of_cors_preflights_from_unknown_origin(self):
        logstream = self.create_logstream()
        origins = (
            'http://beachfront.geointservices.io',  # Not HTTPS
            'http://bf-swagger.geointservices.io',  # Not HTTPS
            'http://instaspotifriendspacebooksterifygram.com',
            'https://beachfront.geointservices.io.totallynotaphishingattempt.com',
            'https://bf-swagger.geointservices.io.totallynotaphishingattempt.com',
        )
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            self.request.headers['Access-Control-Request-Headers'] = 'Content-Type,X-Requested-With'
            self.request.is_xhr = False
            middleware.csrf_filter()
        self.assertEqual([
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`http://beachfront.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`http://bf-swagger.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`http://instaspotifriendspacebooksterifygram.com` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://beachfront.geointservices.io.totallynotaphishingattempt.com` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://bf-swagger.geointservices.io.totallynotaphishingattempt.com` referrer=`None` ip=`1.2.3.4` is_xhr=`True`',
        ], logstream.getvalue().splitlines())

    def test_logs_rejection_of_cors_requests_not_marked_as_xhr(self):
        logstream = self.create_logstream()
        origins = AUTHORIZED_ORIGINS
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = origin
            self.request.is_xhr = False
            middleware.csrf_filter()
        self.assertEqual([
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://beachfront.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://beachfront.dev.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://beachfront.int.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://beachfront.stage.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://beachfront.arbitrary.subdomain.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://bf-swagger.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://bf-swagger.dev.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://bf-swagger.int.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://bf-swagger.stage.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://bf-swagger.arbitrary.subdomain.geointservices.io` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`https://localhost:8080` referrer=`None` ip=`1.2.3.4` is_xhr=`False`',
        ], logstream.getvalue().splitlines())

    def test_logs_rejection_of_cors_requests_that_look_spoofed(self):
        logstream = self.create_logstream()
        origins = AUTHORIZED_ORIGINS
        for origin in origins:
            self.request.reset_mock()
            self.request.path = '/protected'
            self.request.headers['Origin'] = None
            self.request.referrer = origin
            self.request.is_xhr = False
            middleware.csrf_filter()
        self.assertEqual([
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://beachfront.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://beachfront.dev.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://beachfront.int.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://beachfront.stage.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://beachfront.arbitrary.subdomain.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://bf-swagger.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://bf-swagger.dev.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://bf-swagger.int.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://bf-swagger.stage.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://bf-swagger.arbitrary.subdomain.geointservices.io` ip=`1.2.3.4` is_xhr=`False`',
            'WARNING - Possible CSRF attempt: endpoint=`/protected` origin=`None` referrer=`https://localhost:8080` ip=`1.2.3.4` is_xhr=`False`',
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
