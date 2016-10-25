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

class CreateVerifyApiKeyMiddlewareTest(unittest.TestCase):
    def test_validates_api_key_on_every_request(self):
        self.skipTest('Not yet implemented')

    def test_allows_public_endpoints_to_pass_through(self):
        self.skipTest('Not yet implemented')

    def test_throws_when_auth_header_is_missing(self):
        self.skipTest('Not yet implemented')

    def test_throws_when_api_key_is_malformed(self):
        self.skipTest('Not yet implemented')

    def test_returns_http401_if_API_key_is_expired(self):
        self.skipTest('Not yet implemented')

    def test_returns_http500_when_piazza_throw_(self):
        self.skipTest('Not yet implemented')

    def test_returns_http500_on_unexpected_error_(self):
        self.skipTest('Not yet implemented')

    def test_does_not_hijack_next_handlers_errors(self):
        self.skipTest('Not yet implemented')
