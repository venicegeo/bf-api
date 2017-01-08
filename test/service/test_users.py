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
import json
import logging
import unittest
from datetime import datetime
from unittest.mock import patch

import requests
import requests_mock as rm

from bfapi.db import DatabaseError
from bfapi.service import users
from test import helpers

API_KEY = '0123456789abcdef0123456789abcdef'


class AuthenticateViaGeoaxisTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.service.users')
        self._logger.disabled = True
        self._mockdb = helpers.mock_database()

        self.mock_insert_user = self.create_mock('bfapi.db.users.insert_user')
        self.mock_get_by_id = self.create_mock('bfapi.service.users.get_by_id')
        self.mock_requests = rm.Mocker()  # type: rm.Mocker
        self.mock_requests.start()
        self.addCleanup(self.mock_requests.stop)

        self.override_constant('bfapi.service.users.GEOAXIS', 'test-geoaxis')
        self.override_constant('bfapi.service.users.GEOAXIS_CLIENT_ID', 'test-geoaxis-client-id')
        self.override_constant('bfapi.service.users.GEOAXIS_SECRET', 'test-geoaxis-secret')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def override_constant(self, target_name, value):
        patcher = patch(target_name, value)
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

    def test_calls_correct_url_for_token_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = create_user_db_record()
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('https://test-geoaxis/ms_oauth/oauth2/endpoints/oauthservice/tokens',
                         self.mock_requests.request_history[0].url)

    def test_calls_correct_url_for_profile_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = create_user_db_record()
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('https://test-geoaxis/ms_oauth/resources/userprofile/me',
                         self.mock_requests.request_history[1].url)

    def test_sends_correct_payload_to_token_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = create_user_db_record()
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertSetEqual({
            # 'redirect_uri=https%3A%2F%2Fbf-api.localhost',
            'redirect_uri=https%3A%2F%2Fbf-api.int.geointservices.io',  # HACK -- remove this once correct domains get whitelisted
            'code=test-auth-code',
            'grant_type=authorization_code',
        }, set(self.mock_requests.request_history[0].body.split('&')))

    def test_sends_correct_access_token_to_profile_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = create_user_db_record()
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('Bearer test-access-token', self.mock_requests.request_history[1].headers.get('Authorization'))

    def test_creates_new_user_if_not_already_in_database(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertTrue(self.mock_insert_user.called)

    def test_does_not_create_new_user_if_already_in_database(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = users.User(user_id='test-uid', name='test-name')
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertFalse(self.mock_insert_user.called)

    def test_assigns_correct_api_key_to_new_users(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        self.create_mock('uuid.uuid4').return_value.hex = 'lorem ipsum dolor'
        user = users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('lorem ipsum dolor', user.api_key)

    def test_assigns_correct_user_id_to_new_users(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        user = users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('cn=test-commonname, OU=test-org-unit, O=test-org, C=test-country', user.user_id)

    def test_assigns_correct_user_name_to_new_users(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        user = users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('test-commonname', user.name)

    def test_sends_correct_api_key_to_database(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        self.create_mock('uuid.uuid4').return_value.hex = 'lorem ipsum dolor'
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('lorem ipsum dolor', self.mock_insert_user.call_args[1]['api_key'])

    def test_sends_correct_user_dn_to_database(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('cn=test-commonname, OU=test-org-unit, O=test-org, C=test-country', self.mock_insert_user.call_args[1]['user_id'])

    def test_sends_correct_user_name_to_database(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual('test-commonname', self.mock_insert_user.call_args[1]['user_name'])

    def test_returns_an_existing_user(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        existing_user = users.User(user_id='test-uid', name='test-name')
        self.mock_get_by_id.return_value = existing_user
        user = users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual(existing_user, user)

    def test_throws_when_geoaxis_denies_token_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_DENIED, status_code=401)
        with self.assertRaises(users.Unauthorized):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_geoaxis_throws_during_token_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text='oh noes', status_code=500)
        with self.assertRaises(users.GeoaxisError):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_geoaxis_is_unreachable_during_token_request(self):
        self.create_mock('requests.post').side_effect = requests.ConnectionError()
        with self.assertRaises(users.GeoaxisUnreachable):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_geoaxis_denies_profile_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE_UNAUTHORIZED, status_code=401)
        with self.assertRaises(users.Unauthorized):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_geoaxis_throws_during_profile_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text='oh noes', status_code=500)
        with self.assertRaises(users.GeoaxisError):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_geoaxis_is_unreachable_during_profile_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.create_mock('requests.get').side_effect = requests.ConnectionError()
        with self.assertRaises(users.GeoaxisUnreachable):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_access_token_is_missing(self):
        mangled_grant = json.loads(RESPONSE_GEOAXIS_TOKEN_ISSUED)
        del mangled_grant['access_token']
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', json=mangled_grant)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        with self.assertRaisesRegex(users.InvalidGeoaxisResponse, 'missing `access_token`'):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_user_dn_is_missing(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        mangled_profile = json.loads(RESPONSE_GEOAXIS_PROFILE)
        del mangled_profile['DN']
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', json=mangled_profile)
        with self.assertRaisesRegex(users.InvalidGeoaxisResponse, 'missing `DN`'):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_user_name_is_missing(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        mangled_profile = json.loads(RESPONSE_GEOAXIS_PROFILE)
        del mangled_profile['commonname']
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', json=mangled_profile)
        with self.assertRaisesRegex(users.InvalidGeoaxisResponse, 'missing `commonname`'):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_throws_when_database_insertion_fails(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        self.mock_insert_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_geoaxis('test-auth-code')

    def test_logs_success_for_new_user(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        logstream = self.create_logstream()
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'INFO - Creating user account for "cn=test-commonname, OU=test-org-unit, O=test-org, C=test-country"',
            'INFO - User "cn=test-commonname, OU=test-org-unit, O=test-org, C=test-country" has logged in successfully',
        ], logstream.getvalue().splitlines())

    def test_logs_success_for_existing_user(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = create_user_db_record()
        logstream = self.create_logstream()
        users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'INFO - User "cn=test-commonname, OU=test-org-unit, O=test-org, C=test-country" has logged in successfully',
        ], logstream.getvalue().splitlines())

    def test_logs_failure_when_geoaxis_denies_token_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_DENIED, status_code=401)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        logstream = self.create_logstream()
        with self.assertRaises(users.Unauthorized):
            users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'ERROR - GeoAxis rejected user auth code: {',
            '    "error": "invalid_grant",',
            '    "error_description": "Invalid Grant: grant has been revoked; grant_type=azc "',
            '}',
        ], logstream.getvalue().splitlines())

    def test_logs_failure_when_geoaxis_denies_profile_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE_UNAUTHORIZED, status_code=401)
        logstream = self.create_logstream()
        with self.assertRaises(users.Unauthorized):
            users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'ERROR - GeoAxis rejected access token: {',
            '    "message": "Failed in authorization",',
            '    "oicErrorCode": "IDAAS-12345"',
            '}',
        ], logstream.getvalue().splitlines())

    def test_logs_failure_when_geoaxis_throws_during_token_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text='oh noes', status_code=500)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        logstream = self.create_logstream()
        with self.assertRaises(users.GeoaxisError):
            users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'ERROR - GeoAxis returned HTTP 500: oh noes',
        ], logstream.getvalue().splitlines())

    def test_logs_failure_when_geoaxis_throws_during_profile_request(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text='oh noes', status_code=500)
        logstream = self.create_logstream()
        with self.assertRaises(users.GeoaxisError):
            users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'ERROR - GeoAxis returned HTTP 500: oh noes',
        ], logstream.getvalue().splitlines())

    def test_logs_failure_from_database_insert(self):
        self.mock_requests.post('/ms_oauth/oauth2/endpoints/oauthservice/tokens', text=RESPONSE_GEOAXIS_TOKEN_ISSUED)
        self.mock_requests.get('/ms_oauth/resources/userprofile/me', text=RESPONSE_GEOAXIS_PROFILE)
        self.mock_get_by_id.return_value = None
        self.mock_insert_user.side_effect = helpers.create_database_error()
        logstream = self.create_logstream()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_geoaxis('test-auth-code')
        self.assertEqual([
            'INFO - Creating user account for "cn=test-commonname, OU=test-org-unit, O=test-org, C=test-country"',
            'ERROR - Could not save user account "cn=test-commonname, OU=test-org-unit, O=test-org, C=test-country" to database',
        ], logstream.getvalue().splitlines())


class AuthenticateViaApiKeyTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.users')
        self._logger.disabled = True
        self.mock_select_user_by_api_key = self.create_mock('bfapi.db.users.select_user_by_api_key')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def create_mock(self, target_name):
        patcher = patch(target_name)
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

    def test_returns_a_user(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        user = users.authenticate_via_api_key(API_KEY)
        self.assertIsInstance(user, users.User)

    def test_assigns_correct_user_id(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.authenticate_via_api_key(API_KEY)
        self.assertEqual('test-user-id', new_user.user_id)

    def test_assigns_correct_user_name(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.authenticate_via_api_key(API_KEY)
        self.assertEqual('test-user-name', new_user.name)

    def test_assigns_correct_api_key(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.authenticate_via_api_key(API_KEY)
        self.assertEqual(API_KEY, new_user.api_key)

    def test_throws_when_database_query_fails(self):
        self.mock_select_user_by_api_key.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_api_key(API_KEY)

    def test_throws_when_api_key_is_unauthorized(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        with self.assertRaises(users.Unauthorized):
            users.authenticate_via_api_key(API_KEY)

    def test_throws_when_api_key_is_malformed(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        with self.assertRaises(users.MalformedAPIKey):
            users.authenticate_via_api_key('definitely not correctly formed')

    def test_logs_success(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        logstream = self.create_logstream()
        users.authenticate_via_api_key(API_KEY)
        self.assertEqual([
            # Intentionally blank
        ], logstream.getvalue().splitlines())

    def test_logs_failure_from_unauthorized_api_key(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        logstream = self.create_logstream()
        with self.assertRaises(users.Unauthorized):
            users.authenticate_via_api_key(API_KEY)
        self.assertEqual([
            'ERROR - Unauthorized API key "0123456789abcdef0123456789abcdef"'
        ], logstream.getvalue().splitlines())

    def test_logs_failure_from_malformed_api_key(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        logstream = self.create_logstream()
        with self.assertRaises(users.MalformedAPIKey):
            users.authenticate_via_api_key('definitely not correctly formed')
        self.assertEqual([
            'ERROR - Cannot verify malformed API key: "definitely not correctly formed"'
        ], logstream.getvalue().splitlines())

    def test_logs_failure_from_database_select(self):
        self.mock_select_user_by_api_key.side_effect = helpers.create_database_error()
        logstream = self.create_logstream()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_api_key(API_KEY)
        self.assertEqual([
            """ERROR - Database query for API key "0123456789abcdef0123456789abcdef" failed""",
        ], logstream.getvalue().splitlines())


class GetByIdTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.users')
        self._logger.disabled = True
        self.mock_select_user = self.create_mock('bfapi.db.users.select_user')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def create_mock(self, target_name):
        patcher = patch(target_name)
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

    def test_throws_when_database_query_fails(self):
        self.mock_select_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.get_by_id('test-user-id')

    def test_returns_nothing_if_record_not_found(self):
        self.mock_select_user.return_value.fetchone.return_value = None
        user = users.get_by_id('test-user-id')
        self.assertEqual(None, user)

    def test_returns_a_user(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        user = users.get_by_id('test-user-id')
        self.assertIsInstance(user, users.User)

    def test_assigns_correct_user_id(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        user = users.get_by_id('test-user-id')
        self.assertEqual('test-user-id', user.user_id)

    def test_assigns_correct_user_name(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        user = users.get_by_id('test-user-id')
        self.assertEqual('test-user-name', user.name)

    def test_assigns_correct_api_key(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        user = users.get_by_id('test-user-id')
        self.assertEqual(API_KEY, user.api_key)

    def test_logs_database_failure_during_select(self):
        self.mock_select_user.side_effect = helpers.create_database_error()
        logstream = self.create_logstream()
        with self.assertRaises(DatabaseError):
            users.get_by_id('test-user-id')
        self.assertEqual([
            """ERROR - Database query for user ID "test-user-id" failed""",
        ], logstream.getvalue().splitlines())


#
# Helpers
#

def create_user_db_record(user_id: str = 'test-user-id', api_key: str = API_KEY):
    return {
        'user_id': user_id,
        'user_name': 'test-user-name',
        'api_key': api_key,
        'created_on': datetime.utcnow(),
    }

#
# Fixtures
#

RESPONSE_GEOAXIS_PROFILE = """{
    "uid": "test-uid",
    "mail": "test-mail@localhost",
    "username": "test-username",
    "DN": "cn=test-commonname, OU=test-org-unit, O=test-org, C=test-country",
    "email": "test-email@localhost",
    "ID": "test-id",
    "lastname": "test-lastname",
    "login": "test-uid",
    "commonname": "test-commonname",
    "firstname": "test-firstname",
    "personatypecode": "AAA",
    "uri": "/ms_oauth/resources/userprofile/me/test-uid"
}"""

RESPONSE_GEOAXIS_PROFILE_UNAUTHORIZED = """{
    "message": "Failed in authorization",
    "oicErrorCode": "IDAAS-12345"
}"""

RESPONSE_GEOAXIS_TOKEN_ISSUED = """{
    "expires_in": 9999,
    "token_type": "Bearer",
    "access_token": "test-access-token"
}"""

RESPONSE_GEOAXIS_TOKEN_DENIED = """{
    "error": "invalid_grant",
    "error_description": "Invalid Grant: grant has been revoked; grant_type=azc "
}"""
