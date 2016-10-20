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
        with self.assertRaises(piazza.Unauthorized):
            piazza.create_session('Basic Og==')

    def test_throws_when_uuid_is_missing(self, m: Mocker):
        truncated_response = json.loads(RESPONSE_AUTH_SUCCESS)
        truncated_response.pop('uuid')
        m.get('/key', json=truncated_response, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.create_session('Basic Og==')

    def test_throws_when_passed_malformed_auth_header(self, m: Mocker):
        with self.assertRaises(piazza.MalformedSessionToken):
            piazza.create_session('lolwut')


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
        with self.assertRaises(piazza.Unauthorized):
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

    def test_throws_when_passed_malformed_session_token(self, m: Mocker):
        with self.assertRaises(piazza.MalformedSessionToken):
            piazza.get_status('lolwut', 'test-job-id')


@Mocker()
class PiazzaGetServiceTest(unittest.TestCase):
    def test_calls_correct_url(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE)
        piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')
        self.assertEqual(m.request_history[0].url, 'https://pz-gateway.localhost/service/test-id')

    def test_returns_a_service_descriptor(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE)
        descriptor = piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')
        self.assertIsInstance(descriptor, piazza.ServiceDescriptor)

    def test_deserializes_canonical_data(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE)
        descriptor = piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')
        self.assertEqual(descriptor.service_id, 'test-id')
        self.assertEqual(descriptor.description, 'test-description')
        self.assertEqual(descriptor.name, 'test-name')
        self.assertEqual(descriptor.url, 'test-url')

    def test_deserializes_metadata(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE)
        descriptor = piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')
        self.assertEqual(descriptor.metadata, {'classType': {'classification': 'UNCLASSIFIED'}, 'version': 'test-version'})

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')

    def test_throws_when_piazza_is_unreachable(self, m: Mocker):
        self.skipTest('Unsure how to test this one')

    def test_throws_when_service_does_not_exist(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE_NOT_FOUND, status_code=404)
        with self.assertRaises(piazza.ServerError):
            piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')

    def test_throws_when_data_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE)
        mangled_response.pop('data')
        m.get('/service/test-id', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')

    def test_throws_when_data_is_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE)
        mangled_response['data'] = 'lol'
        m.get('/service/test-id', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')

    def test_throws_when_name_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE)
        mangled_response['data']['resourceMetadata'].pop('name')
        m.get('/service/test-id', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')

    def test_throws_when_url_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE)
        mangled_response['data'].pop('url')
        m.get('/service/test-id', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')

    def test_throws_when_descriptors_are_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE)
        mangled_response['data'].pop('serviceId')
        m.get('/service/test-id', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_service('Basic dGVzdC1hdXRoLXRva2VuOg==', service_id='test-id')

    def test_throws_when_passed_malformed_session_token(self, m: Mocker):
        with self.assertRaises(piazza.MalformedSessionToken):
            piazza.get_service('lolwut', service_id='test-id')


@Mocker()
class PiazzaGetServicesTest(unittest.TestCase):
    def test_calls_correct_url(self, m: Mocker):
        m.get('/service', text=RESPONSE_SERVICE_LIST)
        piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')
        self.assertEqual(m.request_history[0].url[0:37], 'https://pz-gateway.localhost/service?')
        self.assertIn('perPage=100', m.request_history[0].url[37:])
        self.assertIn('keyword=%5Etest-pattern%24', m.request_history[0].url[37:])

    def test_returns_a_list_of_service_descriptors(self, m: Mocker):
        m.get('/service', text=RESPONSE_SERVICE_LIST)
        descriptors = piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')
        self.assertIsInstance(descriptors, list)
        self.assertEqual(len(descriptors), 2)

    def test_deserializes_canonical_data(self, m: Mocker):
        m.get('/service', text=RESPONSE_SERVICE_LIST)
        (descriptor, _) = piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')
        self.assertEqual(descriptor.service_id, 'test-id-1')
        self.assertEqual(descriptor.description, 'test-description')
        self.assertEqual(descriptor.name, 'test-name')
        self.assertEqual(descriptor.url, 'test-url')

    def test_deserializes_metadata(self, m: Mocker):
        m.get('/service', text=RESPONSE_SERVICE_LIST)
        (descriptor, _) = piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')
        self.assertEqual(descriptor.metadata, {'classType': {'classification': 'UNCLASSIFIED'}, 'version': 'test-version'})

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.get('/service', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')

    def test_throws_when_piazza_is_unreachable(self, m: Mocker):
        self.skipTest('Unsure how to test this one')

    def test_throws_when_data_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_LIST)
        mangled_response.pop('data')
        m.get('/service', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')

    def test_throws_when_data_is_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_LIST)
        mangled_response['data'] = {}
        m.get('/service', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')

    def test_throws_when_name_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_LIST)
        mangled_response['data'][0]['resourceMetadata'].pop('name')
        mangled_response['data'][1]['resourceMetadata'].pop('name')
        m.get('/service', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')

    def test_throws_when_url_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_LIST)
        mangled_response['data'][0].pop('url')
        mangled_response['data'][1].pop('url')
        m.get('/service', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')

    def test_throws_when_descriptors_are_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_LIST)
        (descriptor, _) = mangled_response['data']
        descriptor.pop('serviceId')
        m.get('/service', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_services('Basic dGVzdC1hdXRoLXRva2VuOg==', pattern='^test-pattern$')

    def test_throws_when_passed_malformed_session_token(self, m: Mocker):
        with self.assertRaises(piazza.MalformedSessionToken):
            piazza.get_services('lolwut', pattern='^test-pattern$')


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
        with self.assertRaises(piazza.MalformedSessionToken):
            piazza.get_username('lolwut')

    def test_throws_when_passed_undecodable_session_token(self, m: Mocker):
        m.post('/v2/verification', text='{}')
        with self.assertRaises(piazza.MalformedSessionToken):
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
        with self.assertRaises(piazza.Unauthorized):
            piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {})

    def test_throws_when_job_id_is_missing(self, m: Mocker):
        truncated_response = json.loads(RESPONSE_JOB_CREATED)
        truncated_response['data'].pop('jobId')
        m.post('/job', json=truncated_response, status_code=201)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.execute('Basic dGVzdC1hdXRoLXRva2VuOg==', 'test-service-id', {})

    def test_throws_when_passed_malformed_session_token(self, m: Mocker):
        with self.assertRaises(piazza.MalformedSessionToken):
            piazza.execute('lolwut', 'test-service-id', {})


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

RESPONSE_SERVICE = """{
  "type": "service",
  "data": {
    "serviceId": "test-id",
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

RESPONSE_SERVICE_NOT_FOUND = """{
  "type": "error",
  "message": "Service not found: test-id",
  "origin": "Service Controller"
}"""
