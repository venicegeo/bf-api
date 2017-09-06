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
import unittest.mock

from requests import ConnectionError, Response
from requests_mock import Mocker

from bfapi.service import piazza

@Mocker()
class CreateTriggerTest(unittest.TestCase):
    maxDiff = 4096

    def setUp(self):
        self._original_api_key = piazza.PIAZZA_API_KEY
        piazza.PIAZZA_API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

    def tearDown(self):
        piazza.PIAZZA_API_KEY = self._original_api_key

    def test_calls_correct_url(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        piazza.create_trigger(
            data_inputs={},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual('https://piazza.test.localdomain/trigger', m.request_history[0].url)

    def test_sends_correct_api_key(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        piazza.create_trigger(
            data_inputs={},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual('Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg==', m.request_history[0].headers['Authorization'])

    def test_sends_correct_payload(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        piazza.create_trigger(
            data_inputs={'lorem': 'ipsum dolor'},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual({
            'name': 'test-name',
            'eventTypeId': 'test-event-type-id',
            'condition': {
                'query': {'query': {'match_all': {}}},
            },
            'job': {
                'jobType': {
                    'type': 'execute-service',
                    'data': {
                        'serviceId': 'test-service-id',
                        'dataInputs': {'lorem': 'ipsum dolor'},
                        'dataOutput': [{
                            'mimeType': 'text/plain',
                            'type': 'text'
                        }],
                    },
                },
            },
            'enabled': True,
        }, m.request_history[0].json())

    def test_returns_trigger_id(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        trigger_id = piazza.create_trigger(
            data_inputs={'foo': 'bar'},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual('test-trigger-id', trigger_id)

    def test_gracefully_handles_errors(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.create_trigger(
                data_inputs={'foo': 'bar'},
                event_type_id='test-event-type-id',
                name='test-name',
                service_id='test-service-id',
            )

    def test_throws_when_piazza_is_unreachable(self, _):
        with unittest.mock.patch('requests.post') as mock:
            mock.side_effect = ConnectionError(request=unittest.mock.Mock())
            with self.assertRaises(piazza.Unreachable):
                piazza.create_trigger(
                    data_inputs={'foo': 'bar'},
                    event_type_id='test-event-type-id',
                    name='test-name',
                    service_id='test-service-id',
                )

    def test_throws_when_data_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_TRIGGER)
        mangled_response.pop('data')
        m.post('/trigger', json=mangled_response, status_code=201)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'missing `data`'):
            piazza.create_trigger(
                data_inputs={'foo': 'bar'},
                event_type_id='test-event-type-id',
                name='test-name',
                service_id='test-service-id',
            )

    def test_throws_when_trigger_id_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_TRIGGER)
        mangled_response['data'].pop('triggerId')
        m.post('/trigger', json=mangled_response, status_code=201)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'missing `data.triggerId`'):
            piazza.create_trigger(
                data_inputs={'foo': 'bar'},
                event_type_id='test-event-type-id',
                name='test-name',
                service_id='test-service-id',
            )

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_AUTH_REJECTED, status_code=401)
        with self.assertRaises(piazza.Unauthorized):
            piazza.create_trigger(
                data_inputs={'foo': 'bar'},
                event_type_id='test-event-type-id',
                name='test-name',
                service_id='test-service-id',
            )


@Mocker()
class ExecuteTest(unittest.TestCase):
    def setUp(self):
        self._original_api_key = piazza.PIAZZA_API_KEY
        piazza.PIAZZA_API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

    def tearDown(self):
        piazza.PIAZZA_API_KEY = self._original_api_key

    def test_calls_correct_url(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('test-service-id', {})
        self.assertEqual('https://piazza.test.localdomain/job', m.request_history[0].url)

    def test_sends_correct_service_id(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('test-service-id', {})
        self.assertEqual('test-service-id', m.request_history[0].json()['data']['serviceId'])

    def test_sends_correct_input_parameters(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('test-service-id', {'foo': 'bar'})
        self.assertEqual({'foo': 'bar'}, m.request_history[0].json()['data']['dataInputs'])

    def test_sends_default_output_parameters(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('test-service-id', {})
        self.assertEqual([{'mimeType': 'application/json', 'type': 'text'}],
                         m.request_history[0].json()['data']['dataOutput'])

    def test_sends_correct_output_parameters_when_explicitly_set(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        piazza.execute('test-service-id', {}, [{'boo': 'baz'}])
        self.assertEqual([{'boo': 'baz'}], m.request_history[0].json()['data']['dataOutput'])

    def test_returns_job_id(self, m: Mocker):
        m.post('/job', text=RESPONSE_JOB_RUNNING, status_code=201)
        job_id = piazza.execute('test-service-id', {'foo': 'bar'}, [{'boo': 'baz'}])
        self.assertEqual('test-job-id', job_id)

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.post('/job', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.execute('test-service-id', {})

    def test_throws_when_piazza_is_unreachable(self, _):
        with unittest.mock.patch('requests.post') as stub:
            stub.side_effect = ConnectionError(request=unittest.mock.Mock())
            with self.assertRaises(piazza.Unreachable):
                piazza.execute('test-service-id', {})

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.post('/job', text=RESPONSE_ERROR_GENERIC, status_code=401)
        with self.assertRaises(piazza.Unauthorized):
            piazza.execute('test-service-id', {})

    def test_throws_when_job_id_is_missing(self, m: Mocker):
        truncated_response = json.loads(RESPONSE_JOB_CREATED)
        truncated_response['data'].pop('jobId')
        m.post('/job', json=truncated_response, status_code=201)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.execute('test-service-id', {})


@Mocker()
class GetFileTest(unittest.TestCase):
    def setUp(self):
        self._original_api_key = piazza.PIAZZA_API_KEY
        piazza.PIAZZA_API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

    def tearDown(self):
        piazza.PIAZZA_API_KEY = self._original_api_key

    def test_calls_correct_urls(self, m: Mocker):
        m.get('/file/test-data-id', text=RESPONSE_FILE)
        piazza.get_file('test-data-id')
        self.assertEqual('https://piazza.test.localdomain/file/test-data-id', m.request_history[0].url)

    def test_sends_correct_api_key(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        piazza.create_trigger(
            data_inputs={},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual('Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg==', m.request_history[0].headers['Authorization'])

    def test_returns_a_response_object(self, m: Mocker):
        m.get('/file/test-data-id', text=RESPONSE_FILE)
        layer_id = piazza.get_file('test-data-id')
        self.assertIsInstance(layer_id, Response)

    def test_returns_response_object_with_correct_contents(self, m: Mocker):
        m.get('/file/test-data-id', text=RESPONSE_FILE)
        response = piazza.get_file('test-data-id')
        self.assertEqual({'foo': 'bar'}, response.json())

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.get('/file/test-data-id', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_file('test-data-id')

    def test_throws_when_piazza_is_unreachable(self, _):
        with unittest.mock.patch('requests.get') as stub:
            stub.side_effect = ConnectionError(request=unittest.mock.Mock())
            with self.assertRaises(piazza.Unreachable):
                piazza.get_file('test-data-id')

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.get('/file/test-data-id', text=RESPONSE_ERROR_GENERIC, status_code=401)
        with self.assertRaises(piazza.Unauthorized):
            piazza.get_file('test-data-id')


@Mocker()
class GetStatusTest(unittest.TestCase):
    def setUp(self):
        self._original_api_key = piazza.PIAZZA_API_KEY
        piazza.PIAZZA_API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

    def tearDown(self):
        piazza.PIAZZA_API_KEY = self._original_api_key

    def test_calls_correct_url(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_RUNNING)
        piazza.get_status('test-job-id')
        self.assertEqual('https://piazza.test.localdomain/job/test-job-id', m.request_history[0].url)

    def test_sends_correct_api_key(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        piazza.create_trigger(
            data_inputs={},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual('Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg==', m.request_history[0].headers['Authorization'])

    def test_returns_correct_status_for_running_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_RUNNING)
        status = piazza.get_status('test-job-id')
        self.assertEqual('Running', status.status)
        self.assertIsNone(status.data_id)
        self.assertIsNone(status.error_message)

    def test_returns_correct_status_for_submitted_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_SUBMITTED)
        status = piazza.get_status('test-job-id')
        self.assertEqual('Submitted', status.status)
        self.assertIsNone(status.data_id)
        self.assertIsNone(status.error_message)

    def test_returns_correct_status_for_pending_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_PENDING)
        status = piazza.get_status('test-job-id')
        self.assertEqual('Pending', status.status)
        self.assertIsNone(status.data_id)
        self.assertIsNone(status.error_message)

    def test_returns_correct_status_for_successful_execution_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_SUCCESS)
        status = piazza.get_status('test-job-id')
        self.assertEqual('Success', status.status)
        self.assertEqual('test-data-id', status.data_id)
        self.assertIsNone(status.error_message)

    def test_returns_correct_status_for_successful_deployment_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_SUCCESS)
        status = piazza.get_status('test-job-id')
        self.assertEqual('Success', status.status)
        self.assertEqual('test-data-id', status.data_id)
        self.assertIsNone(status.error_message)

    def test_returns_correct_status_for_failed_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_ERROR)
        status = piazza.get_status('test-job-id')
        self.assertEqual('Error', status.status)
        self.assertIsNone(status.data_id)
        self.assertEqual('test-failure-message', status.error_message)

    def test_returns_correct_status_for_canceled_job(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_CANCELLED)
        status = piazza.get_status('test-job-id')
        self.assertEqual('Cancelled', status.status)
        self.assertIsNone(status.data_id)
        self.assertIsNone(status.error_message)

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_RUNNING, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_status('test-job-id')

    def test_throws_when_piazza_is_unreachable(self, _):
        with unittest.mock.patch('requests.get') as stub:
            stub.side_effect = ConnectionError(request=unittest.mock.Mock())
            with self.assertRaises(piazza.Unreachable):
                piazza.get_status('test-job-id')

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_ERROR_UNAUTHORIZED, status_code=401)
        with self.assertRaises(piazza.Unauthorized):
            piazza.get_status('test-job-id')

    def test_throws_when_job_doesnt_exist(self, m: Mocker):
        m.get('/job/test-job-id', text=RESPONSE_JOB_NOT_FOUND, status_code=404)
        with self.assertRaises(piazza.ServerError):
            piazza.get_status('test-job-id')

    def test_throws_when_status_is_ambiguous(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_JOB_SUCCESS)
        mangled_response['data']['status'] = 'lolwut'
        m.get('/job/test-job-id', json=mangled_response)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'ambiguous value for `data.status`'):
            piazza.get_status('test-job-id')

    def test_throws_when_deployment_layer_id_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_DEPLOY_SUCCESS)
        mangled_response['data']['result']['deployment'].pop('layer')
        m.get('/job/test-job-id', json=mangled_response)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'missing `data.result.deployment.layer`'):
            piazza.get_status('test-job-id')

    def test_throws_when_deployment_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_DEPLOY_SUCCESS)
        mangled_response['data']['result'].pop('deployment')
        m.get('/job/test-job-id', json=mangled_response)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'missing `data.result.deployment`'):
            piazza.get_status('test-job-id')

    def test_throws_when_status_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_JOB_SUCCESS)
        mangled_response['data'].pop('status')
        m.get('/job/test-job-id', json=mangled_response)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'missing `data.status`'):
            piazza.get_status('test-job-id')

    def test_throws_when_result_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_JOB_SUCCESS)
        mangled_response['data'].pop('result')
        m.get('/job/test-job-id', json=mangled_response)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'missing `data.result`'):
            piazza.get_status('test-job-id')


@Mocker()
class GetServiceTest(unittest.TestCase):
    def setUp(self):
        self._original_api_key = piazza.PIAZZA_API_KEY
        piazza.PIAZZA_API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

    def tearDown(self):
        piazza.PIAZZA_API_KEY = self._original_api_key

    def test_calls_correct_url(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE)
        piazza.get_service(service_id='test-id')
        self.assertEqual('https://piazza.test.localdomain/service/test-id', m.request_history[0].url)

    def test_sends_correct_api_key(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        piazza.create_trigger(
            data_inputs={},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual('Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg==', m.request_history[0].headers['Authorization'])

    def test_returns_a_service_descriptor(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE)
        descriptor = piazza.get_service(service_id='test-id')
        self.assertIsInstance(descriptor, piazza.ServiceDescriptor)

    def test_deserializes_canonical_data(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE)
        descriptor = piazza.get_service(service_id='test-id')
        self.assertEqual('test-id', descriptor.service_id)
        self.assertEqual('test-description', descriptor.description)
        self.assertEqual('test-name', descriptor.name)

    def test_deserializes_metadata(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE)
        descriptor = piazza.get_service(service_id='test-id')
        self.assertEqual({'classType': {'classification': 'UNCLASSIFIED'}, 'version': 'test-version'},
                         descriptor.metadata)

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_service(service_id='test-id')

    def test_throws_when_piazza_is_unreachable(self, _):
        with unittest.mock.patch('requests.get') as stub:
            stub.side_effect = ConnectionError(request=unittest.mock.Mock())
            with self.assertRaises(piazza.Unreachable):
                piazza.get_service(service_id='test-id')

    def test_throws_when_service_does_not_exist(self, m: Mocker):
        m.get('/service/test-id', text=RESPONSE_SERVICE_NOT_FOUND, status_code=404)
        with self.assertRaises(piazza.ServerError):
            piazza.get_service(service_id='test-id')

    def test_throws_when_data_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE)
        mangled_response.pop('data')
        m.get('/service/test-id', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_service(service_id='test-id')

    def test_throws_when_data_is_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE)
        mangled_response['data'] = 'lol'
        m.get('/service/test-id', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_service(service_id='test-id')

    def test_throws_when_name_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE)
        mangled_response['data']['resourceMetadata'].pop('name')
        m.get('/service/test-id', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_service(service_id='test-id')

    def test_throws_when_descriptors_are_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE)
        mangled_response['data'].pop('serviceId')
        m.get('/service/test-id', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_service(service_id='test-id')


@Mocker()
class GetServicesTest(unittest.TestCase):
    def setUp(self):
        self._original_api_key = piazza.PIAZZA_API_KEY
        piazza.PIAZZA_API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

    def tearDown(self):
        piazza.PIAZZA_API_KEY = self._original_api_key

    def test_calls_correct_url(self, m: Mocker):
        m.get('/service', text=RESPONSE_SERVICE_LIST)
        piazza.get_services(pattern='^test-pattern$')
        self.assertEqual('https://piazza.test.localdomain/service?', m.request_history[0].url[:40])
        self.assertIn('perPage=100', m.request_history[0].url[40:])
        self.assertIn('keyword=%5Etest-pattern%24', m.request_history[0].url[40:])

    def test_sends_correct_api_key(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        piazza.create_trigger(
            data_inputs={},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual('Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg==', m.request_history[0].headers['Authorization'])

    def test_returns_a_list_of_service_descriptors(self, m: Mocker):
        m.get('/service', text=RESPONSE_SERVICE_LIST)
        descriptors = piazza.get_services(pattern='^test-pattern$')
        self.assertIsInstance(descriptors, list)
        self.assertEqual(2, len(descriptors))
        self.assertIsInstance(descriptors[0], piazza.ServiceDescriptor)
        self.assertIsInstance(descriptors[1], piazza.ServiceDescriptor)

    def test_deserializes_canonical_data(self, m: Mocker):
        m.get('/service', text=RESPONSE_SERVICE_LIST)
        descriptors = piazza.get_services(pattern='^test-pattern$')
        self.assertEqual('test-id-1', descriptors[0].service_id)
        self.assertEqual('test-description', descriptors[0].description)
        self.assertEqual('test-name', descriptors[0].name)
        self.assertEqual('test-id-2', descriptors[1].service_id)
        self.assertEqual('test-description', descriptors[1].description)
        self.assertEqual('test-name', descriptors[1].name)

    def test_deserializes_metadata(self, m: Mocker):
        m.get('/service', text=RESPONSE_SERVICE_LIST)
        descriptor = piazza.get_services(pattern='^test-pattern$')[0]
        self.assertEqual({'classType': {'classification': 'UNCLASSIFIED'}, 'version': 'test-version'},
                         descriptor.metadata)

    def test_handles_http_errors_gracefully(self, m: Mocker):
        m.get('/service', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_services(pattern='^test-pattern$')

    def test_throws_when_piazza_is_unreachable(self, _):
        with unittest.mock.patch('requests.get') as stub:
            stub.side_effect = ConnectionError(request=unittest.mock.Mock())
            with self.assertRaises(piazza.Unreachable):
                piazza.get_services(pattern='^test-pattern$')

    def test_throws_when_data_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_LIST)
        mangled_response.pop('data')
        m.get('/service', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_services(pattern='^test-pattern$')

    def test_throws_when_data_is_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_LIST)
        mangled_response['data'] = {}
        m.get('/service', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_services(pattern='^test-pattern$')

    def test_throws_when_name_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_LIST)
        mangled_response['data'][0]['resourceMetadata'].pop('name')
        mangled_response['data'][1]['resourceMetadata'].pop('name')
        m.get('/service', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_services(pattern='^test-pattern$')

    def test_throws_when_descriptors_are_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_LIST)
        (descriptor, _) = mangled_response['data']
        descriptor.pop('serviceId')
        m.get('/service', json=mangled_response)
        with self.assertRaises(piazza.InvalidResponse):
            piazza.get_services(pattern='^test-pattern$')


@Mocker()
class GetTriggersTest(unittest.TestCase):
    def setUp(self):
        self._original_api_key = piazza.PIAZZA_API_KEY
        piazza.PIAZZA_API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

    def tearDown(self):
        piazza.PIAZZA_API_KEY = self._original_api_key

    def test_calls_correct_url(self, m: Mocker):
        m.post('/trigger/query', text=RESPONSE_TRIGGER_LIST)
        piazza.get_triggers('test-name')
        self.assertEqual('https://piazza.test.localdomain/trigger/query', m.request_history[0].url)

    def test_sends_correct_api_key(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        piazza.create_trigger(
            data_inputs={},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual('Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg==', m.request_history[0].headers['Authorization'])

    def test_sends_correct_payload(self, m: Mocker):
        m.post('/trigger/query', text=RESPONSE_TRIGGER_LIST)
        piazza.get_triggers('test-name')
        self.assertEqual({
            'query': {
                'match': {
                    'name': 'test-name',
                },
            },
        }, m.request_history[0].json())

    def test_returns_a_list_of_triggers(self, m: Mocker):
        m.post('/trigger/query', text=RESPONSE_TRIGGER_LIST)
        triggers = piazza.get_triggers('test-name')
        self.assertIsInstance(triggers, list)
        self.assertEqual(['test-trigger-id-1', 'test-trigger-id-2'], list(map(lambda d: d['triggerId'], triggers)))

    def test_gracefully_handles_errors(self, m: Mocker):
        m.post('/trigger/query', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.get_triggers('test-name')

    def test_throws_when_data_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_TRIGGER_LIST)
        mangled_response.pop('data')
        m.post('/trigger/query', json=mangled_response)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'missing `data`'):
            piazza.get_triggers('test-name')

    def test_throws_when_response_is_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_TRIGGER_LIST)
        mangled_response['data'] = 'lolwut'
        m.post('/trigger/query', json=mangled_response)
        with self.assertRaisesRegex(piazza.InvalidResponse, '`data` is of the wrong type'):
            piazza.get_triggers('test-name')

    def test_throws_when_piazza_is_unreachable(self, _):
        with unittest.mock.patch('requests.post') as mock:
            mock.side_effect = piazza.Unreachable()
            with self.assertRaises(piazza.Unreachable):
                piazza.get_triggers('test-name')

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.post('/trigger/query', text=RESPONSE_TRIGGER_LIST, status_code=401)
        with self.assertRaises(piazza.Unauthorized):
            piazza.get_triggers('test-name')


@Mocker()
class RegisterServiceTest(unittest.TestCase):
    maxDiff = 4096

    def setUp(self):
        self._original_api_key = piazza.PIAZZA_API_KEY
        piazza.PIAZZA_API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'

    def tearDown(self):
        piazza.PIAZZA_API_KEY = self._original_api_key

    def test_calls_correct_url(self, m: Mocker):
        m.post('/service', text=RESPONSE_SERVICE_REGISTERED, status_code=201)
        piazza.register_service(
            contract_url='test-contract-url',
            description='test-description',
            name='test-name',
            url='test-url',
        )
        self.assertEqual('https://piazza.test.localdomain/service', m.request_history[0].url)

    def test_sends_correct_api_key(self, m: Mocker):
        m.post('/trigger', text=RESPONSE_TRIGGER, status_code=201)
        piazza.create_trigger(
            data_inputs={},
            event_type_id='test-event-type-id',
            name='test-name',
            service_id='test-service-id',
        )
        self.assertEqual('Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg==', m.request_history[0].headers['Authorization'])

    def test_sends_correct_payload(self, m: Mocker):
        m.post('/service', text=RESPONSE_SERVICE_REGISTERED, status_code=201)
        piazza.register_service(
            contract_url='test-contract-url',
            description='test-description',
            name='test-name',
            url='test-url',
        )
        self.assertEqual({
            'url': 'test-url',
            'contractUrl': 'test-contract-url',
            'method': 'POST',
            'timeout': 60,
            'resourceMetadata': {
                'name': 'test-name',
                'description': 'test-description',
                'version': '0.0',
                'classType': {
                    'classification': 'Unclassified',
                },
            },
        }, m.request_history[0].json())

    def test_returns_service_id(self, m: Mocker):
        m.post('/service', text=RESPONSE_SERVICE_REGISTERED, status_code=201)
        service_id = piazza.register_service(
            contract_url='test-contract-url',
            description='test-description',
            name='test-name',
            url='test-url',
        )
        self.assertEqual('test-service-id', service_id)

    def test_gracefully_handles_errors(self, m: Mocker):
        m.post('/service', text=RESPONSE_ERROR_GENERIC, status_code=500)
        with self.assertRaises(piazza.ServerError):
            piazza.register_service(
                contract_url='test-contract-url',
                description='test-description',
                name='test-name',
                url='test-url',
            )

    def test_throws_when_data_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_REGISTERED)
        mangled_response.pop('data')
        m.post('/service', json=mangled_response, status_code=201)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'missing `data`'):
            piazza.register_service(
                contract_url='test-contract-url',
                description='test-description',
                name='test-name',
                url='test-url',
            )

    def test_throws_when_service_id_is_missing(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_REGISTERED)
        mangled_response['data'].pop('serviceId')
        m.post('/service', json=mangled_response, status_code=201)
        with self.assertRaisesRegex(piazza.InvalidResponse, 'missing `data.serviceId`'):
            piazza.register_service(
                contract_url='test-contract-url',
                description='test-description',
                name='test-name',
                url='test-url',
            )

    def test_throws_when_response_is_malformed(self, m: Mocker):
        mangled_response = json.loads(RESPONSE_SERVICE_REGISTERED)
        mangled_response['data'] = 'lolwut'
        m.post('/service', json=mangled_response, status_code=201)
        with self.assertRaisesRegex(piazza.InvalidResponse, '`data` is of the wrong type'):
            piazza.register_service(
                contract_url='test-contract-url',
                description='test-description',
                name='test-name',
                url='test-url',
            )

    def test_throws_when_piazza_is_unreachable(self, _):
        with unittest.mock.patch('requests.post') as mock:
            mock.side_effect = ConnectionError(request=unittest.mock.Mock())
            with self.assertRaises(piazza.Unreachable):
                piazza.register_service(
                    contract_url='test-contract-url',
                    description='test-description',
                    name='test-name',
                    url='test-url',
                )

    def test_throws_when_credentials_are_rejected(self, m: Mocker):
        m.post('/service', text=RESPONSE_AUTH_REJECTED, status_code=401)
        with self.assertRaises(piazza.Unauthorized):
            piazza.register_service(
                contract_url='test-contract-url',
                description='test-description',
                name='test-name',
                url='test-url',
            )


#
# Fixtures
#

RESPONSE_AUTH_ACTIVE = """{
    "type": "auth",
    "isAuthSuccess": true,
    "userProfile": {
        "username": "test-username"
    }
}"""

RESPONSE_AUTH_EXPIRED = """{
    "type": "auth",
    "isAuthSuccess": false
}"""

RESPONSE_AUTH_REJECTED = """{
    "type": "error",
    "message": "Authentication failed for user test-username",
    "origin": "IDAM"
}"""

RESPONSE_AUTH_SUCCESS = """{
    "type": "uuid",
    "uuid": "test-uuid"
}"""

RESPONSE_DEPLOY_SUCCESS = """{
  "type": "status",
  "data": {
    "result": {
      "type": "deployment",
      "deployment": {
        "deploymentId": "test-deployment-id",
        "dataId": "test-data-id",
        "host": "test-host",
        "port": "test-port",
        "layer": "test-layer-id",
        "capabilitiesUrl": "test-capabilities-url",
        "createdOn": "test-created-on"
      }
    },
    "status": "Success",
    "jobType": "AccessJob",
    "createdBy": "test-created-by",
    "progress": {},
    "jobId": "test-job-id"
  }
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

RESPONSE_FILE = """{"foo":"bar"}"""

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

RESPONSE_JOB_PENDING = """{
  "type": "status",
  "data": {
    "status": "Pending",
    "jobType": "ExecuteServiceJob",
    "createdBy": "test-username",
    "createdOn": "2017-01-19T22:01:34.251Z",
    "executedServiceId": "a209c8dd-7dbf-49ce-b83d-18aded5ef8e3",
    "progress": {},
    "jobId": "test-job-id"
  }
}"""

RESPONSE_JOB_SUBMITTED = """{
  "type": "status",
  "data": {
    "result": null,
    "status": "Submitted",
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
    "isTaskManaged": false,
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
      "isTaskManaged": false,
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
      "url": null,
      "contractUrl": "test-contract-url",
      "method": "POST",
      "isTaskManaged": true,
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

RESPONSE_SERVICE_REGISTERED = """{
  "type": "service-id",
  "data": {
    "serviceId": "test-service-id"
  }
}"""

RESPONSE_SERVICE_UNREGISTERED = """{
  "type": "success",
  "data": {
    "message": "Service was deleted successfully.",
    "origin": "ServiceController"
  }
}"""

RESPONSE_TRIGGER_ERROR = """{
  "type": "error",
  "message": "TriggerDB.PostData failed: serviceID test-service-id does not exist",
  "origin": "pz-workflow"
}"""

RESPONSE_TRIGGER = r"""{
  "type": "trigger",
  "data": {
    "triggerId": "test-trigger-id",
    "name": "test-trigger-name",
    "eventTypeId": "test-event-type-id",
    "condition": {
      "query": {
        "query": {
          "match_all": {}
        }
      }
    },
    "job": {
      "createdBy": "test-created-by",
      "jobType": {
        "data": {
          "dataInputs": {
            "foo": {
              "content": null,
              "type": "text",
              "mimeType": "text/plain"
            }
          },
          "dataOutput": [
            {
              "content": null,
              "mimeType": "text/plain",
              "type": "text"
            }
          ],
          "serviceId": "test-service-id"
        },
        "type": "execute-service"
      }
    },
    "percolationId": "",
    "createdBy": "test-created-by",
    "createdOn": "2016-11-05T23:29:54.189286813Z",
    "enabled": true
  }
}"""

RESPONSE_TRIGGER_LIST = """{
  "type": "trigger-list",
  "data": [
    {
      "triggerId": "test-trigger-id-1",
      "name": "test-trigger-name",
      "condition": {
        "query": {
          "bool": {
            "filter": null
          }
        }
      },
      "eventTypeId": "test-event-type-id",
      "job": {
        "createdBy": "test-created-by",
        "jobType": {
          "type": "execute-service",
          "data": {
            "serviceId": "test-service-id",
            "dataInputs": {
              "foo": {
                "type": "text",
                "content": null,
                "mimeType": "text/plain"
              }
            },
            "dataOutput": [
              {
                "type": "text",
                "content": null,
                "mimeType": "text/plain"
              }
            ]
          }
        }
      },
      "percolationId": "",
      "createdBy": "test-created-by",
      "enabled": true,
      "createdOn": "2016-10-17T13:25:29.246Z"
    },
    {
      "triggerId": "test-trigger-id-2",
      "name": "test-trigger-name",
      "condition": {
        "query": {
          "bool": {
            "filter": null
          }
        }
      },
      "eventTypeId": "test-event-type-id",
      "job": {
        "createdBy": "test-created-by",
        "jobType": {
          "type": "execute-service",
          "data": {
            "serviceId": "test-service-id",
            "dataInputs": {
              "foo": {
                "type": "text",
                "content": null,
                "mimeType": "text/plain"
              }
            },
            "dataOutput": [
              {
                "type": "text",
                "content": null,
                "mimeType": "text/plain"
              }
            ]
          }
        }
      },
      "percolationId": "",
      "createdBy": "test-created-by",
      "enabled": true,
      "createdOn": "2016-10-17T13:25:29.246Z"
    }
  ]
}"""
