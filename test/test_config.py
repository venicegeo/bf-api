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

import os
import unittest
from datetime import timedelta

from bfapi import config


class ConfigurationValueTest(unittest.TestCase):
    def test_autodetects_piazza_hostname(self):
        self.assertEqual('piazza.test.localdomain', config.PIAZZA)

    def test_autodetects_catalog_hostname(self):
        self.assertEqual('bf-ia-broker.test.localdomain', config.CATALOG)

    def test_defines_sensible_job_ttl(self):
        self.assertGreaterEqual(config.JOB_TTL, timedelta(seconds=600))

    def test_defines_sensible_job_polling_frequency(self):
        self.assertGreaterEqual(config.JOB_WORKER_INTERVAL, timedelta(seconds=15))


class ConfigurationValidateTest(unittest.TestCase):
    def setUp(self):
        self._original_values = {}
        self.override('_errors', [])
        self.override('PIAZZA_API_KEY', 'test-api-key')
        self.override('POSTGRES_HOST', 'test-host')
        self.override('POSTGRES_PORT', 'test-port')
        self.override('POSTGRES_DATABASE', 'test-database')
        self.override('POSTGRES_USERNAME', 'test-username')
        self.override('POSTGRES_PASSWORD', 'test-password')
        self.override('GEOSERVER_HOST', 'test-host')
        self.override('GEOSERVER_USERNAME', 'test-username')
        self.override('GEOSERVER_PASSWORD', 'test-password')
        self.override('GEOAXIS', 'test-host')
        self.override('GEOAXIS_CLIENT_ID', 'test-client-id')
        self.override('GEOAXIS_SECRET', 'test-secret')

    def tearDown(self):
        for key, value in self._original_values.items():
            setattr(config, key, value)

    def override(self, key: str, value: any):
        self._original_values[key] = value
        setattr(config, key, value)

    def test_succeeds_if_config_is_valid(self):
        config.validate(failfast=False)

    def test_throws_if_PIAZZA_API_KEY_is_blank(self):
        self.override('PIAZZA_API_KEY', None)
        with self.assertRaises(Exception):
            config.validate(failfast=False)

    def test_throws_if_POSTGRES_HOST_is_blank(self):
        self.override('POSTGRES_HOST', None)
        with self.assertRaises(Exception):
            config.validate(failfast=False)

    def test_throws_if_POSTGRES_PORT_is_blank(self):
        self.override('POSTGRES_PORT', None)
        with self.assertRaises(Exception):
            config.validate(failfast=False)

    def test_throws_if_POSTGRES_DATABASE_is_blank(self):
        self.override('POSTGRES_DATABASE', None)
        with self.assertRaises(Exception):
            config.validate(failfast=False)

    def test_throws_if_POSTGRES_USERNAME_is_blank(self):
        self.override('POSTGRES_USERNAME', None)
        with self.assertRaises(Exception):
            config.validate(failfast=False)

    def test_throws_if_POSTGRES_PASSWORD_is_blank(self):
        self.override('POSTGRES_PASSWORD', None)
        with self.assertRaises(Exception):
            config.validate(failfast=False)

    def test_throws_if_GEOSERVER_HOST_is_blank(self):
        self.override('GEOSERVER_HOST', None)
        with self.assertRaises(Exception):
            config.validate(failfast=False)

    def test_throws_if_GEOSERVER_USERNAME_is_blank(self):
        self.override('GEOSERVER_USERNAME', None)
        with self.assertRaises(Exception):
            config.validate(failfast=False)

    def test_throws_if_GEOSERVER_PASSWORD_is_blank(self):
        self.override('GEOSERVER_PASSWORD', None)
        with self.assertRaises(Exception):
            config.validate(failfast=False)


class ConfigureGetServices(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self._VCAP_SERVICES = os.getenv('VCAP_SERVICES')
        self._original_errors = config._errors

    def tearDown(self):
        self.override(self._VCAP_SERVICES)
        config._errors = self._original_errors

    def override(self, value):
        if value is None:
            if 'VCAP_SERVICES' in os.environ:
                os.environ.pop('VCAP_SERVICES')
        else:
            os.environ['VCAP_SERVICES'] = value

    def test_always_returns_a_dictionary(self):
        self.assertIsInstance(config._getservices(), dict)

    def test_returns_defined_services(self):
        self.override(
            """
            {
              "user-provided": [
                {
                  "name": "test-service-1",
                  "credentials": {
                    "database": "test-database",
                    "host": "test-host",
                    "hostname": "test-hostname",
                    "password": "test-password",
                    "port": "test-port",
                    "username": "test-username"
                  }
                },
                {
                  "name": "test-service-2",
                  "lorem": "ipsum",
                  "some": {
                    "arbitrarily": {
                      "nested": "value"
                    }
                  }
                }
              ]
            }
            """)
        self.assertEqual(
            {
                'test-service-1.name': 'test-service-1',
                'test-service-1.credentials.database': 'test-database',
                'test-service-1.credentials.host': 'test-host',
                'test-service-1.credentials.hostname': 'test-hostname',
                'test-service-1.credentials.username': 'test-username',
                'test-service-1.credentials.password': 'test-password',
                'test-service-1.credentials.port': 'test-port',
                'test-service-2.name': 'test-service-2',
                'test-service-2.lorem': 'ipsum',
                'test-service-2.some.arbitrarily.nested': 'value',
            },
            config._getservices())

    def test_flags_error_if_VCAP_SERVICES_is_blank(self):
        self.override(None)
        config._getservices()
        self.assertIn('VCAP_SERVICES cannot be blank', config._errors)

    def test_flags_error_if_VCAP_SERVICES_is_malformed(self):
        self.override('lolwut')
        config._getservices()
        self.assertIn('VCAP_SERVICES cannot be blank', config._errors)

    def test_flags_error_if_service_name_is_missing(self):
        self.override(
            """
            {
              "user-provided": [
                {
                  "lorem": "ipsum"
                }
              ]
            }
            """)
        self.assertIn('VCAP_SERVICES cannot be blank', config._errors)
        self.assertEqual({}, config._getservices())

    def test_flags_error_if_user_services_are_absent(self):
        self.override(
            """
            {
              "lolwut-provided": [
                {
                  "name": "test-service-2",
                  "lorem": "ipsum"
                }
              ]
            }
            """)
        self.assertIn('VCAP_SERVICES cannot be blank', config._errors)
        self.assertEqual({}, config._getservices())
