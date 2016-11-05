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

from bfapi import db


class GetConnectionTest(unittest.TestCase):
    def setUp(self):
        self.conn = unittest.mock.Mock()

    def test_does_things(self):
        self.fail('Not implemented')


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.conn = unittest.mock.Mock()

    def test_does_things(self):
        self.fail('Not implemented')
