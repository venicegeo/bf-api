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

import unittest.mock

from bfapi.db import user as userdb


class SelectUserTest(unittest.TestCase):
    def setUp(self):
        self.conn = unittest.mock.Mock()

    def test_sends_correct_query(self):
        self.skipTest('Not implemented')

    def test_sends_correct_parameters(self):
        self.skipTest('Not implemented')

    def test_throws_when_connection_throws(self):
        self.skipTest('Not implemented')


class SelectUserByApiKeyTest(unittest.TestCase):
    def setUp(self):
        self.conn = unittest.mock.Mock()

    def test_sends_correct_query(self):
        self.skipTest('Not implemented')

    def test_sends_correct_parameters(self):
        self.skipTest('Not implemented')

    def test_throws_when_connection_throws(self):
        self.skipTest('Not implemented')


class InsertUserTest(unittest.TestCase):
    def setUp(self):
        self.conn = unittest.mock.Mock()

    def test_sends_correct_query(self):
        self.skipTest('Not implemented')

    def test_sends_correct_parameters(self):
        self.skipTest('Not implemented')

    def test_throws_when_connection_throws(self):
        self.skipTest('Not implemented')


class UpdateUserTest(unittest.TestCase):
    def setUp(self):
        self.conn = unittest.mock.Mock()

    def test_sends_correct_query(self):
        self.skipTest('Not implemented')

    def test_sends_correct_parameters(self):
        self.skipTest('Not implemented')

    def test_throws_when_connection_throws(self):
        self.skipTest('Not implemented')
