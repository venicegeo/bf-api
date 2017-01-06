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
from datetime import datetime
from unittest.mock import patch

import requests
import requests_mock as rm

from bfapi.config import GEOAXIS
from bfapi.db import DatabaseError
from bfapi.service import users
from test import helpers

GEOAXIS_USERPROFILE_URL = 'https://{}/ms_oauth/resources/userprofile/me'.format(GEOAXIS)


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

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_creates_new_user_if_not_already_in_database(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-token')
        self.assertTrue(self.mock_insert_user.called)

    def test_does_not_create_new_user_if_already_in_database(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        self.mock_get_by_id.return_value = users.User(user_id='test-uid', name='test-name')
        users.authenticate_via_geoaxis('test-token')
        self.assertFalse(self.mock_insert_user.called)

    def test_assigns_correct_api_key_to_new_users(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        self.mock_get_by_id.return_value = None
        self.create_mock('uuid.uuid4').return_value = 'lorem ipsum dolor'
        user = users.authenticate_via_geoaxis('test-token')
        self.assertEqual('lorem ipsum dolor', user.api_key)

    def test_assigns_correct_user_id_to_new_users(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        self.mock_get_by_id.return_value = None
        user = users.authenticate_via_geoaxis('test-token')
        self.assertEqual('test-id', user.user_id)

    def test_assigns_correct_user_name_to_new_users(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        self.mock_get_by_id.return_value = None
        user = users.authenticate_via_geoaxis('test-token')
        self.assertEqual('test-name', user.name)

    def test_sends_correct_api_key_to_database(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        self.mock_get_by_id.return_value = None
        self.create_mock('uuid.uuid4').return_value = 'lorem ipsum dolor'
        users.authenticate_via_geoaxis('test-token')
        self.assertEqual('lorem ipsum dolor', self.mock_insert_user.call_args[1]['api_key'])

    def test_sends_correct_user_id_to_database(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-token')
        self.assertEqual('test-id', self.mock_insert_user.call_args[1]['user_id'])

    def test_sends_correct_user_name_to_database(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        self.mock_get_by_id.return_value = None
        users.authenticate_via_geoaxis('test-token')
        self.assertEqual('test-name', self.mock_insert_user.call_args[1]['user_name'])

    def test_returns_an_existing_user(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        existing_user = users.User(user_id='test-uid', name='test-name')
        self.mock_get_by_id.return_value = existing_user
        user = users.authenticate_via_geoaxis('test-token')
        self.assertEqual(existing_user, user)

    def test_throws_when_geoaxis_is_unreachable(self):
        mock_request_get = self.create_mock('requests.get')
        mock_request_get.side_effect = requests.ConnectionError()
        with self.assertRaises(users.GeoaxisUnreachable):
            users.authenticate_via_geoaxis('test-token')

    def test_throws_when_geoaxis_returns_unauthorized(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='resp', status_code=401)
        with self.assertRaises(users.GeoaxisUnauthorized):
            users.authenticate_via_geoaxis('test-token')

    def test_throws_when_geoaxis_throws(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='resp', status_code=500)
        with self.assertRaisesRegex(users.GeoaxisError, 'HTTP 500'):
            users.authenticate_via_geoaxis('test-token')

    def test_throws_when_uid_is_missing(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"username":"test-name"}')
        with self.assertRaises(users.InvalidGeoaxisResponse):
            users.authenticate_via_geoaxis('test-token')

    def test_throws_when_username_is_missing(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id"}')
        with self.assertRaises(users.InvalidGeoaxisResponse):
            users.authenticate_via_geoaxis('test-token')

    def test_throws_when_database_insertion_fails(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}')
        self.mock_get_by_id.return_value = None
        self.mock_insert_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_geoaxis('test-token')



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


    def test_returns_a_user(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        user = users.authenticate_via_api_key('test-api-key')
        self.assertIsInstance(user, users.User)

    def test_assigns_correct_user_id(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.authenticate_via_api_key('test-api-key')
        self.assertEqual('test-user-id', new_user.user_id)

    def test_assigns_correct_user_name(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.authenticate_via_api_key('test-api-key')
        self.assertEqual('test-user-name', new_user.name)

    def test_assigns_correct_api_key(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.authenticate_via_api_key('test-api-key')
        self.assertEqual('test-api-key', new_user.api_key)

    def test_throws_when_database_query_fails(self):
        self.mock_select_user_by_api_key.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_api_key('test-api-key')

    def test_throws_when_on_failed_auth(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        with self.assertRaises(users.BeachfrontUnauthorized):
            users.authenticate_via_api_key('test-api-key')


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
        self.assertEqual('test-api-key', user.api_key)


#
# Helpers
#

def create_user_db_record(user_id: str = 'test-user-id', api_key: str = 'test-api-key'):
    return {
        'user_id': user_id,
        'user_name': 'test-user-name',
        'api_key': api_key,
        'created_on': datetime.utcnow(),
    }
