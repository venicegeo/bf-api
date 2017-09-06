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
from unittest.mock import patch, MagicMock

from bfapi.service import algorithms, piazza


@patch('bfapi.service.piazza.get_services')
class ListAllTest(unittest.TestCase):
    def test_requests_algorithms_from_piazza(self, mock: MagicMock):
        algorithms.list_all()
        self.assertEqual(('BF_Algo_',), mock.call_args[0])

    def test_returns_list_of_algorithms(self, mock: MagicMock):
        mock.return_value = [create_service()]
        items = algorithms.list_all()
        self.assertIsInstance(items, list)
        self.assertIsInstance(items[0], algorithms.Algorithm)

    def test_can_handle_empty_result_set(self, mock: MagicMock):
        mock.return_value = []
        self.assertEqual([], algorithms.list_all())

    def test_can_handle_multiple_results(self, mock: MagicMock):
        mock.return_value = [
            create_service('test-algo-1'),
            create_service('test-algo-2'),
            create_service('test-algo-3'),
        ]
        items = algorithms.list_all()
        self.assertEqual(['test-algo-1', 'test-algo-2', 'test-algo-3'], list(map(lambda a: a.service_id, items)))

    def test_extracts_correct_interface(self, mock: MagicMock):
        mock.return_value = [create_service()]
        algo = algorithms.list_all().pop()
        self.assertEqual('test-interface', algo.interface)

    def test_extracts_correct_description(self, mock: MagicMock):
        mock.return_value = [create_service()]
        algo = algorithms.list_all().pop()
        self.assertEqual('test-description', algo.description)

    def test_extracts_correct_max_cloud_cover(self, mock: MagicMock):
        mock.return_value = [create_service()]
        algo = algorithms.list_all().pop()
        self.assertEqual(42, algo.max_cloud_cover)

    def test_extracts_correct_name(self, mock: MagicMock):
        mock.return_value = [create_service()]
        algo = algorithms.list_all().pop()
        self.assertEqual('test-name', algo.name)

    def test_extracts_correct_service_id(self, mock: MagicMock):
        mock.return_value = [create_service()]
        algo = algorithms.list_all().pop()
        self.assertEqual('test-service-id', algo.service_id)

    def test_extracts_correct_version(self, mock: MagicMock):
        mock.return_value = [create_service()]
        algo = algorithms.list_all().pop()
        self.assertEqual('test-version', algo.version)

    def test_discards_services_missing_interface(self, mock: MagicMock):
        service = create_service()
        service.metadata['metadata'].pop('Interface')
        mock.return_value = [service]
        self.assertEqual([], algorithms.list_all())

    def test_discards_services_missing_max_cloud_cover(self, mock: MagicMock):
        service = create_service()
        service.metadata['metadata'].pop('ImgReq - cloudCover')
        mock.return_value = [service]
        self.assertEqual([], algorithms.list_all())

    def test_discards_services_missing_metadata(self, mock: MagicMock):
        service = create_service()
        service.metadata.pop('metadata')
        mock.return_value = [service]
        self.assertEqual([], algorithms.list_all())

    def test_discards_services_missing_version(self, mock: MagicMock):
        service = create_service()
        service.metadata.pop('version')
        mock.return_value = [service]
        self.assertEqual([], algorithms.list_all())

    def test_discards_services_with_invalid_max_cloud_cover(self, mock: MagicMock):
        service = create_service()
        service.metadata['metadata']['ImgReq - cloudCover'] = 'lolwut'
        mock.return_value = [service]
        self.assertEqual([], algorithms.list_all())

    def test_throws_when_piazza_throws(self, mock: MagicMock):
        mock.side_effect = piazza.Unauthorized()
        with self.assertRaises(piazza.Unauthorized):
            algorithms.list_all()


@patch('bfapi.service.piazza.get_service')
class GetTest(unittest.TestCase):
    def test_requests_algorithms_from_piazza(self, mock: MagicMock):
        mock.return_value = create_service()
        algorithms.get('test-service-id')
        self.assertEqual(('test-service-id',), mock.call_args[0])

    def test_returns_an_algorithm(self, mock: MagicMock):
        mock.return_value = create_service()
        self.assertIsInstance(algorithms.get('test-service-id'), algorithms.Algorithm)

    def test_throws_when_service_not_found(self, mock: MagicMock):
        mock.side_effect = piazza.ServerError(404)
        with self.assertRaises(algorithms.NotFound):
            algorithms.get('test-service-id')

    def test_extracts_correct_interface(self, mock: MagicMock):
        mock.return_value = create_service()
        algo = algorithms.get('test-service-id')
        self.assertEqual('test-interface', algo.interface)

    def test_extracts_correct_description(self, mock: MagicMock):
        mock.return_value = create_service()
        algo = algorithms.get('test-service-id')
        self.assertEqual('test-description', algo.description)

    def test_extracts_correct_max_cloud_cover(self, mock: MagicMock):
        mock.return_value = create_service()
        algo = algorithms.get('test-service-id')
        self.assertEqual(42, algo.max_cloud_cover)

    def test_extracts_correct_name(self, mock: MagicMock):
        mock.return_value = create_service()
        algo = algorithms.get('test-service-id')
        self.assertEqual('test-name', algo.name)

    def test_extracts_correct_service_id(self, mock: MagicMock):
        mock.return_value = create_service()
        algo = algorithms.get('test-service-id')
        self.assertEqual('test-service-id', algo.service_id)

    def test_extracts_correct_version(self, mock: MagicMock):
        mock.return_value = create_service()
        algo = algorithms.get('test-service-id')
        self.assertEqual('test-version', algo.version)

    def test_throws_if_missing_interface(self, mock: MagicMock):
        service = create_service()
        service.metadata['metadata'].pop('Interface')
        mock.return_value = service
        with self.assertRaisesRegex(algorithms.ValidationError, 'missing `Interface`'):
            algorithms.get('test-service-id')

    def test_throws_if_missing_max_cloud_cover(self, mock: MagicMock):
        service = create_service()
        service.metadata['metadata'].pop('ImgReq - cloudCover')
        mock.return_value = service
        with self.assertRaisesRegex(algorithms.ValidationError, 'missing `cloudCover`'):
            algorithms.get('test-service-id')

    def test_throws_if_missing_metadata(self, mock: MagicMock):
        service = create_service()
        service.metadata.pop('metadata')
        mock.return_value = service
        with self.assertRaisesRegex(algorithms.ValidationError, 'missing `metadata` hash'):
            algorithms.get('test-service-id')

    def test_throws_if_missing_version(self, mock: MagicMock):
        service = create_service()
        service.metadata.pop('version')
        mock.return_value = service
        with self.assertRaisesRegex(algorithms.ValidationError, 'missing `version`'):
            algorithms.get('test-service-id')

    def test_throws_if_with_invalid_max_cloud_cover(self, mock: MagicMock):
        service = create_service()
        service.metadata['metadata']['ImgReq - cloudCover'] = 'lolwut'
        mock.return_value = service
        with self.assertRaisesRegex(algorithms.ValidationError, 'not a number'):
            algorithms.get('test-service-id')

    def test_throws_when_piazza_throws(self, mock: MagicMock):
        mock.side_effect = piazza.Unauthorized()
        with self.assertRaises(piazza.Unauthorized):
            algorithms.get('test-service-id')


#
# Helpers
#

def create_service(service_id: str = 'test-service-id'):
    return piazza.ServiceDescriptor(
        description='test-description',
        metadata={
            'metadata': {
                'ImgReq - bands': 'test-band1,test-band2',
                'ImgReq - cloudCover': '42',
                'Interface': 'test-interface',
            },
            'version': 'test-version',
        },
        name='test-name',
        service_id=service_id,
    )
