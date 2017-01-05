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
import uuid
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime


import requests
import requests_mock as rm
from test import helpers
from bfapi import piazza
from bfapi.service import users
from bfapi.db import DatabaseError
from bfapi.config import GEOAXIS

GEOAXIS_USERPROFILE_URL = 'https://{}/ms_oauth/resources/userprofile/me'.format(GEOAXIS)

class AuthenticateViaGeoaxisTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.service.users')
        self._logger.disabled = True
        self._mockdb = helpers.mock_database()

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
        
    def test_throws_on_connection_error(self):
        mock_request_get = self.create_mock('requests.get')
        mock_request_get.side_effect = requests.ConnectionError()
        with self.assertRaises(users.GeoaxisUnreachable):
            users.authenticate_via_geoaxis('test-token')

    def test_throws_on_unauthorized(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='resp', status_code=401)
        with self.assertRaises(users.GeoaxisUnauthorized):
            users.authenticate_via_geoaxis('test-token')

    def test_throws_on_http_error(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='resp', status_code=405)
        with self.assertRaises(users.GeoaxisError):
            users.authenticate_via_geoaxis('test-token')
        
    def test_throws_on_no_uid(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"username":"test-name"}', status_code=200)
        with self.assertRaises(users.InvalidGeoaxisResponse):
            users.authenticate_via_geoaxis('test-token')
        
    def test_throws_on_no_user_name(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id"}', status_code=200)
        with self.assertRaises(users.InvalidGeoaxisResponse):
            users.authenticate_via_geoaxis('test-token')
        
    def test_throws_on_dbase_error(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}', status_code=200)
        mock_insert_update = self.create_mock('bfapi.db.users.insert_or_update_user')
        mock_insert_update.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_geoaxis('test-token')
        
    def test_returns_user(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}', status_code=200)
        mock_insert_update = self.create_mock('bfapi.db.users.insert_or_update_user')
        mock_get_by_id = self.create_mock('bfapi.service.users.get_by_id')
        inp_user = users.User(user_id = "test-uid", user_name = "test-user_name")
        mock_get_by_id.return_value = inp_user
        outp_user = users.authenticate_via_geoaxis('test-token')
        self.assertIsInstance(outp_user, users.User)
        self.assertEqual(inp_user, outp_user)

    def test_correct_user_id_to_insert_update(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}', status_code=200)
        mock_insert_update = self.create_mock('bfapi.db.users.insert_or_update_user')
        mock_get_by_id = self.create_mock('bfapi.service.users.get_by_id')
        inp_user = users.User(user_id = "test-uid", user_name = "test-user_name")
        mock_get_by_id.return_value = inp_user
        outp_user = users.authenticate_via_geoaxis('test-token')
        self.assertEqual("test-id",  mock_insert_update.call_args[1]["user_id"])
        
    def test_correct_user_name_to_insert_update(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}', status_code=200)
        mock_insert_update = self.create_mock('bfapi.db.users.insert_or_update_user')
        mock_get_by_id = self.create_mock('bfapi.service.users.get_by_id')
        inp_user = users.User(user_id = "test-uid", user_name = "test-user_name")
        mock_get_by_id.return_value = inp_user
        outp_user = users.authenticate_via_geoaxis('test-token')
        self.assertEqual("test-name",  mock_insert_update.call_args[1]["user_name"])
        
    def test_correct_should_force_to_insert_update(self):
        self.mock_requests.get(GEOAXIS_USERPROFILE_URL, text='{"uid":"test-id","username":"test-name"}', status_code=200)
        mock_insert_update = self.create_mock('bfapi.db.users.insert_or_update_user')
        mock_get_by_id = self.create_mock('bfapi.service.users.get_by_id')
        inp_user = users.User(user_id = "test-uid", user_name = "test-user_name")
        mock_get_by_id.return_value = inp_user
        outp_user = users.authenticate_via_geoaxis('test-token')
        self.assertEqual(False,  mock_insert_update.call_args[1]["should_force_api_key"])


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
        
    def test_throws_on_db_error(self):
        self.mock_select_user_by_api_key.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.authenticate_via_api_key('test-api_key')
        
    def test_throws_on_failed_auth(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = None
        with self.assertRaises(users.BeachfrontUnauthorized):
            users.authenticate_via_api_key('test-api_key')
        
    def test_verifies_api_key(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        with self.assertRaises(users.DatabaseMismatchError):
            users.authenticate_via_api_key('not-the-returned-api_key')
        
    def test_assigns_correct_user_id(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record(api_key='test-api_key')
        new_user = users.authenticate_via_api_key('test-api_key')
        self.assertIsInstance(new_user, users.User)
        self.assertEqual('test-user-id', new_user.user_id)

    def test_assigns_correct_user_name(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record(api_key='test-api_key')
        new_user = users.authenticate_via_api_key('test-api_key')
        self.assertIsInstance(new_user, users.User)
        self.assertEqual('test-user-name', new_user.user_name)

    def test_assigns_correct_api_key(self):
        self.mock_select_user_by_api_key.return_value.fetchone.return_value = create_user_db_record(api_key='test-api_key')
        new_user = users.authenticate_via_api_key('test-api_key')
        self.assertIsInstance(new_user, users.User)
        self.assertEqual('test-api_key', new_user.bf_api_key)

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
        
    def test_throws_on_db_error(self):
        self.mock_select_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            users.get_by_id('test-user-id')
        
    def test_returns_nothing_if_record_not_found(self):
        self.mock_select_user.return_value.fetchone.return_value = None
        new_user = users.get_by_id('test-user-id')
        self.assertEqual(None, new_user)
        
    def test_throws_on_wrong_id(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        with self.assertRaises(users.DatabaseMismatchError):
            users.get_by_id('not-the-returned-geoaxis-id')

    def test_assigns_correct_user_id(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.get_by_id('test-user-id')
        self.assertIsInstance(new_user, users.User)
        self.assertEqual('test-user-id', new_user.user_id)

    def test_assigns_correct_user_name(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.get_by_id('test-user-id')
        self.assertIsInstance(new_user, users.User)
        self.assertEqual('test-user-name', new_user.user_name)

    def test_assigns_correct_api_key(self):
        self.mock_select_user.return_value.fetchone.return_value = create_user_db_record()
        new_user = users.get_by_id('test-user-id')
        self.assertIsInstance(new_user, users.User)
        self.assertEqual('test-key', new_user.bf_api_key)

#
# Helpers
#
def create_user_db_record(user_id: str = 'test-user-id', api_key: str = 'test-key'):
    return {
        'user_id': user_id,
        'user_name': 'test-user-name',
        'api_key': api_key,
        'created_on': datetime.utcnow(),
    }
