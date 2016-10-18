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

import json
import unittest

from requests_mock import Mocker

from bfapi import piazza


@Mocker()
class PiazzaGetUsernameTest(unittest.TestCase):
    def test_calls_correct_url(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_GET_USERNAME_SUCCESS)
        piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')
        self.assertEqual(m.request_history[0].url, 'https://pz-idam.localhost/v2/verification')

    def test_sends_correct_payload(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_GET_USERNAME_SUCCESS)
        piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')
        self.assertEqual(m.request_history[0].json(), {'uuid': 'test-auth-token'})

    def test_returns_correct_username(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_GET_USERNAME_SUCCESS)
        username = piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')
        self.assertEqual(username, 'test-username')

    def test_throws_when_session_is_not_current(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_GET_USERNAME_FAILURE)
        with self.assertRaises(piazza.SessionExpired):
            piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')

    def test_throws_when_username_is_missing(self, m: Mocker):
        truncated_response = json.loads(RESPONSE_GET_USERNAME_SUCCESS)
        truncated_response.pop('username')
        m.post('/v2/verification', json=truncated_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')

    def test_throws_when_piazza_throws(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_GENERIC_ERROR, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')

    def test_throws_when_piazza_is_unreachable(self, m: Mocker):
        self.skipTest('Unsure how to test this one')

    def test_throws_when_passed_malformed_session_token(self, m: Mocker):
        m.post('/v2/verification', text='{}')
        with self.assertRaises(piazza.AuthenticationError):
            piazza.get_username('lolwut')

    def test_throws_when_passed_undecodable_session_token(self, m: Mocker):
        m.post('/v2/verification', text='{}')
        with self.assertRaises(piazza.AuthenticationError):
            piazza.get_username('Basic lolwut')


@Mocker()
class PiazzaCreateSessionTest(unittest.TestCase):
    def test_calls_correct_url(self, m: Mocker):
        m.get('/key', text=RESPONSE_CREATE_SESSION_SUCCESS)
        piazza.create_session('Basic Og==')
        self.assertEqual(m.request_history[0].url, 'https://pz-gateway.localhost/key')

    def test_sends_correct_payload(self, m: Mocker):
        m.get('/key', text=RESPONSE_CREATE_SESSION_SUCCESS)
        piazza.create_session('Basic Og==')
        self.assertEqual(m.request_history[0].headers.get('Authorization'), 'Basic Og==')

    def test_returns_correct_session_token(self, m: Mocker):
        m.get('/key', text=RESPONSE_CREATE_SESSION_SUCCESS)
        token = piazza.create_session('Basic Og==')
        self.assertEqual(token, 'Basic dGVzdC11dWlkOg==')

    def test_throws_when_piazza_is_unreachable(self, m: Mocker):
        self.skipTest('Unsure how to test this one')

    def test_throws_when_piazza_throws(self, m: Mocker):
        m.get('/key', text=RESPONSE_GENERIC_ERROR, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.create_session('Basic Og==')

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.get('/key', text=RESPONSE_CREATE_SESSION_FAILURE, status_code=401)
        with self.assertRaises(piazza.AuthenticationError):
            piazza.create_session('Basic Og==')

    def test_throws_when_uuid_is_missing(self, m: Mocker):
        truncated_response = json.loads(RESPONSE_CREATE_SESSION_SUCCESS)
        truncated_response.pop('uuid')
        m.get('/key', json=truncated_response, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.create_session('Basic Og==')


#
# Fixtures
#

RESPONSE_CREATE_SESSION_SUCCESS = """{
    "type": "uuid",
    "uuid": "test-uuid"
}"""

RESPONSE_CREATE_SESSION_FAILURE = """{
    "type": "error",
    "message": "Authentication failed for user pztestpass09",
    "origin": "IDAM"
}"""

RESPONSE_GET_USERNAME_SUCCESS = """{
    "type": "auth",
    "username": "test-username",
    "authenticated": true
}"""

RESPONSE_GET_USERNAME_FAILURE = """{
    "type": "auth",
    "authenticated": false
}"""

RESPONSE_GENERIC_ERROR = """{
    "type": "error",
    "origin": "someplace"
}"""
