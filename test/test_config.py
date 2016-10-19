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

from bfapi import config

class ConfigurationTest(unittest.TestCase):
    def test_autodetects_piazza_gateway(self):
        self.assertIn('pz-gateway.', config.PZ_GATEWAY)

    def test_autodetects_catalog_url(self):
        self.assertIn('pzsvc-image-catalog.', config.CATALOG)

    def test_autodetects_tideprediction_url(self):
        self.assertIn('bf-tideprediction.', config.TIDE_SERVICE)
