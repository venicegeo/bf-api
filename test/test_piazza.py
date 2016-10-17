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

import unittest

import requests_mock as rm

from bfapi import piazza


@rm.Mocker()
class PiazzaGetUsernameTest(unittest.TestCase):
    def test_calls_correct_url(self, m: rm.Mocker):
        m.post('/v2/verification', json=_respond_session_active())
        piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')
        self.assertEqual(m.request_history[0].url, 'https://pz-idam.localhost/v2/verification')

    def test_sends_correct_payload(self, m: rm.Mocker):
        m.post('/v2/verification', json=_respond_session_active())
        piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')
        self.assertEqual(m.request_history[0].json(), {'uuid': 'test-auth-token'})

    def test_returns_correct_username(self, m: rm.Mocker):
        m.post('/v2/verification', json=_respond_session_active())
        username = piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')
        self.assertEqual(username, 'test-username')

    def test_throws_when_session_is_not_current(self, m: rm.Mocker):
        m.post('/v2/verification', json=_respond_session_expired())
        with self.assertRaises(piazza.SessionExpired):
            piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')

    def test_throws_when_username_is_missing(self, m: rm.Mocker):
        truncated_response = _respond_session_active()
        truncated_response.pop('username')
        m.post('/v2/verification', json=truncated_response)
        with self.assertRaises(piazza.InvalidResponseError):
            piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')

    def test_throws_when_piazza_throws(self, m: rm.Mocker):
        m.post('/v2/verification', status_code=500, json={'type': 'error'})
        with self.assertRaises(piazza.AuthError):
            piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')

    def test_throws_when_piazza_is_unreachable(self, m: rm.Mocker):
        self.skipTest('Unsure how to test this one')

    def test_throws_when_passed_malformed_session_token(self, m: rm.Mocker):
        m.post('/v2/verification', json={})
        with self.assertRaises(piazza.AuthError):
            piazza.get_username('lolwut')

    def test_throws_when_passed_undecodable_session_token(self, m: rm.Mocker):
        m.post('/v2/verification', json={})
        with self.assertRaises(piazza.AuthError):
            piazza.get_username('Basic lolwut')


#
# Helpers
#

def _respond_session_active():
    return {
        "type": "auth",
        "username": "test-username",
        "authenticated": True
    }


def _respond_session_expired():
    return {
        "type": "auth",
        "authenticated": False
    }
