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
from unittest.mock import patch

from test import helpers

from bfapi.db import DatabaseError
from bfapi.service import JWT_Transcipher


class DecryptJWTTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.REPLACE_WITH_SERVICE')
        self._logger.disabled = True
        self.override_constant('bfapi.service.JWT_Transcipher.SECRET_KEY', 'test-secret')

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

    def test_returns_payload(self):
        payload=JWT_Transcipher.decrypt('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmb28iOiJiYXIifQ.7mqDjNFzZNRDT3hdsKjbnAIymSzjpF_Bu5GMWPrP4o4')
        self.assertEqual({'foo':'bar'}, payload)

class EncryptJWTTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.REPLACE_WITH_SERVICE')
        self._logger.disabled = True
        self.override_constant('bfapi.service.JWT_Transcipher.SECRET_KEY', 'test-secret')
        self.mock_insert_key = self.create_mock('bfapi.db.secret.insert_one_time_key')
        self.mock_use_key = self.create_mock('bfapi.db.secret.find_and_mark_one_time_key_used')
        self.mock_exists_key = self.create_mock('bfapi.db.secret.check_if_one_time_key_exists')

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
    
    def test_returns_jwt(self):
        jwt=JWT_Transcipher.encrypt({"foo": "bar"})
        payload=JWT_Transcipher.decrypt(jwt)
        self.assertEqual({"foo": "bar","JWT_OTU": None}, payload)
    
    def test_returns_jwt_one_time_use(self):
        jwt=JWT_Transcipher.encrypt({"foo": "bar","JWT_OTU": "yes"})
        payload=JWT_Transcipher.decrypt(jwt)
        payload=JWT_Transcipher.decrypt(jwt)
        