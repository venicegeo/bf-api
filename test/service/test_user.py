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
from unittest.mock import patch, MagicMock
from datetime import datetime


import requests
import requests_mock as rm
from test import helpers
from bfapi import piazza
from bfapi.service import user
from bfapi.db import DatabaseError


class GeoaxisTokenLoginTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.user')
        self._logger.disabled = True

        self.mock_requests = rm.Mocker()  # type: rm.Mocker
        self.mock_requests.start()
        self.addCleanup(self.mock_requests.stop)
        #self.mock_insert_job = self.create_mock('bfapi.db.user.insert_job')
        #self.mock_insert_job_user = self.create_mock('bfapi.db.user.insert_job_user')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False
        
    def test_throws_on_connection_error(self):
        self.skipTest('Not implemented')
        
    def test_throws_on_http_error(self):
        self.skipTest('Not implemented')
        
    def test_throws_on_no_uid(self):
        self.skipTest('Not implemented')
        
    def test_throws_on_no_user_name(self):
        self.skipTest('Not implemented')
        
    def test_successful_run(self):
        self.skipTest('Not implemented')

class NewApiKeyTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.user')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False
        
    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_returns_correct_api_key(self):
        # sets up necessary mocks
        # calls new_api_key, keeps return
        # checks mock for the posted information.  Retrieves api key
        # compares.  Verifies that they are the same.
        self.skipTest('Not implemented')

    def test_throws_on_blank_uid(self):
        self.skipTest('Not implemented')

class LoginByApiKeyTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.user')
        self._logger.disabled = True
        self.mock_get_user_by_api_key = self.create_mock('bfapi.db.user.select_user_by_api_key')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False
        
    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()
        
    def test_throws_on_db_error(self):
        self.mock_get_user_by_api_key.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            user.login_by_api_key('test-api_key')
        
    def test_return_none_if_none(self):
        self.mock_get_user_by_api_key.return_value.fetchone.return_value = None
        new_user = user.login_by_api_key('test-api_key')
        self.assertEqual(None, new_user)
        
    def test_verifies_api_key(self):
        self.mock_get_user_by_api_key.return_value.fetchone.return_value = create_user_db_record()
        with self.assertRaises(Exception):
            new_user = user.login_by_api_key('not-the-returned-api_key')
        
    def test_return_user_if_good_row(self):
        self.mock_get_user_by_api_key.return_value.fetchone.return_value = create_user_db_record(api_key='test-api_key')
        new_user = user.login_by_api_key('test-api_key')
        self.assertIsInstance(new_user, user.User)
        self.assertEqual('test-user-id', new_user.geoaxis_uid)
        self.assertEqual('test-user-name', new_user.user_name)
        self.assertEqual('test-api_key', new_user.bf_api_key)

class GetByIdTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.user')
        self._logger.disabled = True
        self.mock_get_user = self.create_mock('bfapi.db.user.select_user')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()
        
    def test_throws_on_db_error(self):
        self.mock_get_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            user.get_by_id('test-user-id')
        
    def test_return_none_if_none(self):
        self.mock_get_user.return_value.fetchone.return_value = None
        new_user = user.get_by_id('test-user-id')
        self.assertEqual(None, new_user)
        
    def test_return_user_if_row(self):
        self.mock_get_user.return_value.fetchone.return_value = create_user_db_record()
        new_user = user.get_by_id('test-user-id')
        self.assertIsInstance(new_user, user.User)
        self.assertEqual('test-user-id', new_user.geoaxis_uid)
        self.assertEqual('test-user-name', new_user.user_name)
        self.assertEqual('test-key', new_user.bf_api_key)
        
class DbHarmonizeTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.user')
        self._logger.disabled = True
        self.mock_get_user = self.create_mock('bfapi.db.user.select_user')
        self.mock_insert_user = self.create_mock('bfapi.db.user.insert_user')
        self.mock_update_user = self.create_mock('bfapi.db.user.update_user')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False
        
    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_throws_on_blank_user(self):
        with self.assertRaises(Exception):
            user._db_harmonize(None)
        
    def test_new_user_throws_on_db_error(self):
        self.mock_get_user.return_value.fetchone.return_value = None
        self.mock_insert_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            user._db_harmonize(user.User(geoaxis_uid='testId', user_name='test_name'))
        
    def test_new_user_successful_submit(self):
        self.mock_get_user.return_value.fetchone.return_value = None
        self.skipTest('Not implemented')
        
    def test_repeat_user_throws_on_db_error(self):
        self.mock_get_user.return_value.fetchone.return_value = create_user_db_record()
        self.mock_update_user.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            user._db_harmonize(user.User(geoaxis_uid='testId', user_name='test_name'))
        
    def test_repeat_user_successful_update(self):
        self.mock_get_user.return_value.fetchone.return_value = create_user_db_record()
        self.skipTest('Not implemented')

#
# Helpers
#
def create_user_db_record(geoaxis_uid: str = 'test-user-id', api_key: str = 'test-key'):
    return {
        'geoaxis_uid': geoaxis_uid,
        'user_name': 'test-user-name',
        'api_key': api_key,
        'created_on': datetime.utcnow(),
    }