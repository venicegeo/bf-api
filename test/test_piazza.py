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

import json
import unittest

from requests_mock import Mocker

from bfapi import piazza


@Mocker()
class PiazzaCreateSessionTest(unittest.TestCase):
    def test_calls_correct_url(self, m: Mocker):
        m.get('/key', text=RESPONSE_AUTH_SUCCESS)
        piazza.create_session('Basic Og==')
        self.assertEqual(m.request_history[0].url, 'https://pz-gateway.localhost/key')

    def test_sends_correct_payload(self, m: Mocker):
        m.get('/key', text=RESPONSE_AUTH_SUCCESS)
        piazza.create_session('Basic Og==')
        self.assertEqual(m.request_history[0].headers.get('Authorization'), 'Basic Og==')

    def test_returns_correct_session_token(self, m: Mocker):
        m.get('/key', text=RESPONSE_AUTH_SUCCESS)
        token = piazza.create_session('Basic Og==')
        self.assertEqual(token, 'Basic dGVzdC11dWlkOg==')

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.get('/key', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.create_session('Basic Og==')

    def test_throws_when_piazza_is_unreachable(self, m: Mocker):
        self.skipTest('Unsure how to test this one')

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.get('/key', text=RESPONSE_AUTH_REJECTED, status_code=401)
        with self.assertRaises(piazza.AuthenticationError):
            piazza.create_session('Basic Og==')

    def test_throws_when_uuid_is_missing(self, m: Mocker):
        truncated_response = json.loads(RESPONSE_AUTH_SUCCESS)
        truncated_response.pop('uuid')
        m.get('/key', json=truncated_response, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.create_session('Basic Og==')


@Mocker()
class PiazzaGetStatusTest(unittest.TestCase):
    def test_calls_correct_url(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_RUNNING)
        piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')
        self.assertEqual(m.request_history[0].url, 'https://pz-gateway.localhost/job/test-job-id')

    def test_returns_correct_status_for_running_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_RUNNING)
        status = piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')
        self.assertEqual(status.status, 'Running')
        self.assertIsNone(status.data_id)
        self.assertIsNone(status.error_message)

    def test_returns_correct_status_for_successful_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_SUCCESS)
        status = piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')
        self.assertEqual(status.status, 'Success')
        self.assertEqual(status.data_id, 'test-data-id')
        self.assertIsNone(status.error_message)

    def test_returns_correct_status_for_failed_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_ERROR)
        status = piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')
        self.assertEqual(status.status, 'Error')
        self.assertIsNone(status.data_id)
        self.assertEqual(status.error_message, 'test-failure-message')

    def test_returns_correct_status_for_canceled_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_CANCELLED)
        status = piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')
        self.assertEqual(status.status, 'Cancelled')
        self.assertIsNone(status.data_id)
        self.assertIsNone(status.error_message)

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_RUNNING, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')

    def test_throws_when_piazza_is_unreachable(self, m: Mocker):
        self.skipTest('Unsure how to test this one')

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_ERROR_UNAUTHORIZED, status_code=401)
        with self.assertRaises(piazza.AuthenticationError):
            piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')

    def test_throws_when_job_doesnt_exist(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_NOT_FOUND, status_code=404)
        with self.assertRaises(piazza.ServerError):
            piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')

    def test_throws_when_status_is_ambiguous(self, m: Mocker):
        mutated_status = json.loads(RESPONSE_JOB_SUCCESS)
        mutated_status['data']['status'] = 'lolwut'
        m.get('/job/test-job-id', json=mutated_status)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')

    def test_throws_when_status_is_missing(self, m: Mocker):
        mutated_status = json.loads(RESPONSE_JOB_SUCCESS)
        mutated_status['data'].pop('status')
        m.get('/job/test-job-id', json=mutated_status)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')

    def test_throws_when_result_is_missing(self, m: Mocker):
        mutated_status = json.loads(RESPONSE_JOB_SUCCESS)
        mutated_status['data'].pop('result')
        m.get('/job/test-job-id', json=mutated_status)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_status('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-job-id')


@Mocker()
class PiazzaGetUsernameTest(unittest.TestCase):
    def test_calls_correct_url(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_AUTH_ACTIVE)
        piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')
        self.assertEqual(m.request_history[0].url, 'https://pz-idam.localhost/v2/verification')

    def test_sends_correct_payload(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_AUTH_ACTIVE)
        piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')
        self.assertEqual(m.request_history[0].json(), {'uuid': 'test-auth-token'})

    def test_returns_correct_username(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_AUTH_ACTIVE)
        username = piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')
        self.assertEqual(username, 'test-username')

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')

    def test_throws_when_session_is_not_current(self, m: Mocker):
        m.post('/v2/verification', text=RESPONSE_AUTH_EXPIRED)
        with self.assertRaises(piazza.SessionExpired):
            piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')

    def test_throws_when_username_is_missing(self, m: Mocker):
        truncated_response = json.loads(RESPONSE_AUTH_ACTIVE)
        truncated_response.pop('username')
        m.post('/v2/verification', json=truncated_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_username('Basic dGVzdC1hdXRoLXRva2VuOg==')

    def test_throws_when_piazza_is_unreachable(self, m: Mocker):
        self.skipTest('Unsure how to test this one')

    def test_throws_when_passed_malformed_session_token(self, m: Mocker):
        m.post('/v2/verification', text='{}')
        with self.assertRaises(piazza.AuthenticationError):
            piazza.get_username('lolwut')

    def test_throws_when_passed_undecodable_session_token(self, m: Mocker):
        m.post('/v2/verification', text='{}')
        with self.assertRaises(piazza.AuthenticationError):
            piazza.get_username('Basic lolwut')


@Mocker()
class PiazzaExecuteTest(unittest.TestCase):
    def test_calls_correct_url(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {})
        self.assertEqual(m.request_history[0].url, 'https://pz-gateway.localhost/job')

    def test_sends_correct_service_id(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {})
        self.assertEqual(m.request_history[0].json()['data']['serviceId'], 'test-service-id')

    def test_sends_correct_input_parameters(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {'foo': 'bar'})
        self.assertEqual(m.request_history[0].json()['data']['dataInputs'], {'foo': 'bar'})

    def test_sends_default_output_parameters(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {})
        self.assertEqual(m.request_history[0].json()['data']['dataOutput'],
                         [{'mimeType': 'application/json', 'type': 'text'}])

    def test_sends_correct_output_parameters_when_explicitly_set(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {}, [{'boo': 'baz'}])
        self.assertEqual(m.request_history[0].json()['data']['dataOutput'], [{'boo': 'baz'}])

    def test_returns_job_id(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        job_id = piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {'foo': 'bar'}, [{'boo': 'baz'}])
        self.assertEqual(job_id, 'test-job-id')

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.post('/job', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {})

    def test_throws_when_piazza_is_unreachable(self, m: Mocker):
        self.skipTest('Unsure how to test this one')

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.post('/job', text=RESPONSE_ERROR_GENERIC, status_code=401)
        with self.assertRaises(piazza.AuthenticationError):
            piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {})

    def test_throws_when_job_id_is_missing(self, m: Mocker):
        truncated_response = json.loads(RESPONSE_JOB_CREATED)
        truncated_response['data'].pop('jobId')
        m.post('/job', json=truncated_response, status_code=201)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {})


#
# Fixtures
#

RESPONSE_AUTH_ACTIVE = """{
    "type": "auth",
    "username": "test-username",
    "authenticated": true
}"""

RESPONSE_AUTH_EXPIRED = """{
    "type": "auth",
    "authenticated": false
}"""

RESPONSE_AUTH_REJECTED = """{
    "type": "error",
    "message": "Authentication failed for user pztestpass09",
    "origin": "IDAM"
}"""

RESPONSE_AUTH_SUCCESS = """{
    "type": "uuid",
    "uuid": "test-uuid"
}"""

RESPONSE_ERROR_UNAUTHORIZED = """{
  "type": "error",
  "message": "Gateway is unable to authenticate the provided user.",
  "origin": "Gateway"
}"""

RESPONSE_ERROR_GENERIC = """{
    "type": "error",
    "origin": "someplace"
}"""

RESPONSE_JOB_CANCELLED = """{
  "type": "status",
  "data": {
    "result": null,
    "status": "Cancelled",
    "jobType": "ExecuteServiceJob",
    "createdBy": "test-username",
    "progress": {},
    "jobId": "test-job-id"
  }
}"""

RESPONSE_JOB_CREATED = """{
  "type": "job",
  "data": {
    "jobId": "test-job-id"
  }
}"""

RESPONSE_JOB_ERROR = """{
  "type": "status",
  "data": {
    "result": {
      "type": "error",
      "message": "test-failure-message"
    },
    "status": "Error",
    "jobType": "ExecuteServiceJob",
    "createdBy": "test-username",
    "progress": {},
    "jobId": "test-job-id"
  }
}"""

RESPONSE_JOB_NOT_FOUND = """{
  "type": "error",
  "message": "Job not found: test-job-id",
  "origin": "Job Manager"
}"""

RESPONSE_JOB_RUNNING = """{
  "type": "status",
  "data": {
    "result": null,
    "status": "Running",
    "jobType": "ExecuteServiceJob",
    "createdBy": "test-username",
    "progress": {},
    "jobId": "test-job-id"
  }
}"""

RESPONSE_JOB_SUCCESS = """{
  "type": "status",
  "data": {
    "result": {
      "type": "data",
      "dataId": "test-data-id"
    },
    "status": "Success",
    "jobType": "ExecuteServiceJob",
    "createdBy": "test-username",
    "progress": {},
    "jobId": "test-job-id"
  }
}"""

RESPONSE_SERVICE_LIST = """{
  "type": "service-list",
  "data": [
    {
      "serviceId": "test-id-1",
      "url": "test-url",
      "contractUrl": "test-contract-url",
      "method": "POST",
      "resourceMetadata": {
        "name": "test-name",
        "description": "test-description",
        "classType": {
          "classification": "UNCLASSIFIED"
        },
        "version": "test-version"
      }
    },
    {
      "serviceId": "test-id-2",
      "url": "test-url",
      "contractUrl": "test-contract-url",
      "method": "POST",
      "resourceMetadata": {
        "name": "test-name",
        "description": "test-description",
        "availability": "test-availability",
        "classType": {
          "classification": "UNCLASSIFIED"
        },
        "version": "test-version"
      }
    }
  ],
  "pagination": {
    "count": 2,
    "page": 0,
    "per_page": 100
  }
}"""
