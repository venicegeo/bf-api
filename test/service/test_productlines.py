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
from datetime import datetime
from unittest.mock import patch, MagicMock

from test import helpers

from bfapi import piazza
from bfapi.db import DatabaseError
from bfapi.service import productlines
from bfapi.service.algorithms import Algorithm, NotFound, ValidationError
from bfapi.service.jobs import Job

DATE_START = datetime.fromtimestamp(1400000000)
DATE_STOP = datetime.fromtimestamp(1500000000)
SIGNATURE = '723d038b797360ef90f5a848a910aea4f5b2d8b680d443745cb2e6667faee2ea4581040d2639f0ff35c8dbc1c8ac8188'


class CreateEventSignatureTest(unittest.TestCase):
    def test_returns_correct_fingerprint(self):
        self.assertEqual(productlines.create_event_signature(), SIGNATURE)

    @patch('hashlib.sha384')
    def test_uses_hashing_to_generate(self, mock: MagicMock):
        productlines.create_event_signature()
        mock.assert_called_once_with('None:pz-gateway.localhost'.encode())


@patch('bfapi.service.algorithms.get')
class CreateProductlineTest(unittest.TestCase):
    maxDiff = 1024

    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.productlines')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_returns_productline(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertIsInstance(record, productlines.ProductLine)

    def test_assigns_auto_generated_id(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertRegex(record.productline_id, r'^[a-z]+$')

    def test_assigns_correct_algorithm_name(self, mock: MagicMock):
        mock.return_value = create_algorithm()
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual('test-algo-name', record.algorithm_name)

    def test_assigns_correct_bbox(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual([[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]],
                         record.bbox['coordinates'])

    def test_assigns_correct_category(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual('test-category', record.category)

    def test_assigns_correct_creator(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual('test-user-id', record.created_by)

    def test_assigns_correct_creation_date(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual(datetime.utcnow().date(), record.created_on.date())

    def test_assigns_correct_max_cloud_cover(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual(42, record.max_cloud_cover)

    def test_assigns_correct_name(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual('test-name', record.name)

    def test_assigns_correct_owner(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual('test-user-id', record.owned_by)

    def test_assigns_correct_spatial_filter_id(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual('test-spatial-filter-id', record.spatial_filter_id)

    def test_assigns_correct_start_date(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual(DATE_START.isoformat(), record.start_on.isoformat())

    def test_assigns_correct_stop_date(self, _):
        record = productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        self.assertEqual(DATE_STOP.isoformat(), record.stop_on.isoformat())

    @patch('bfapi.db.productlines.insert_productline')
    def test_saves_correct_data_to_database(self, mock_insert: MagicMock, mock_get_algo: MagicMock):
        mock_get_algo.return_value = create_algorithm()
        productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        _, args = mock_insert.call_args
        self.assertRegex(args['productline_id'], '^[a-z]+$')
        self.assertEqual('test-algo-id', args['algorithm_id'])
        self.assertEqual('test-algo-name', args['algorithm_name'])
        self.assertEqual((0, 0, 30, 30), args['bbox'])
        self.assertEqual('test-category', args['category'])
        self.assertEqual(42, args['max_cloud_cover'])
        self.assertEqual('test-name', args['name'])
        self.assertEqual('test-spatial-filter-id', args['spatial_filter_id'])
        self.assertEqual(DATE_START, args['start_on'])
        self.assertEqual(DATE_STOP, args['stop_on'])
        self.assertEqual('test-user-id', args['user_id'])

    def test_requests_correct_algorithm(self, mock: MagicMock):
        mock.return_value = create_algorithm()
        productlines.create_productline(
            api_key='test-api-key',
            algorithm_id='test-algo-id',
            bbox=(0, 0, 30, 30),
            category='test-category',
            max_cloud_cover=42,
            name='test-name',
            spatial_filter_id='test-spatial-filter-id',
            start_on=DATE_START,
            stop_on=DATE_STOP,
            user_id='test-user-id',
        )
        mock.assert_called_with('test-api-key', 'test-algo-id')

    def test_gracefully_handles_algorithm_not_found(self, mock: MagicMock):
        mock.side_effect = NotFound('test-algo-id')
        with self.assertRaisesRegex(NotFound, 'algorithm `test-algo-id` does not exist'):
            productlines.create_productline(
                api_key='test-api-key',
                algorithm_id='test-algo-id',
                bbox=(0, 0, 30, 30),
                category='test-category',
                max_cloud_cover=42,
                name='test-name',
                spatial_filter_id='test-spatial-filter-id',
                start_on=DATE_START,
                stop_on=DATE_STOP,
                user_id='test-user-id',
            )

    def test_gracefully_handles_algorithm_validation_error(self, mock: MagicMock):
        mock.side_effect = ValidationError('test-error-message')
        with self.assertRaises(ValidationError):
            productlines.create_productline(
                api_key='test-api-key',
                algorithm_id='test-algo-id',
                bbox=(0, 0, 30, 30),
                category='test-category',
                max_cloud_cover=42,
                name='test-name',
                spatial_filter_id='test-spatial-filter-id',
                start_on=DATE_START,
                stop_on=DATE_STOP,
                user_id='test-user-id',
            )

    def test_gracefully_handles_database_error(self, _):
        self._mockdb.raise_on_execute()
        with self.assertRaises(DatabaseError):
            productlines.create_productline(
                api_key='test-api-key',
                algorithm_id='test-algo-id',
                bbox=(0, 0, 30, 30),
                category='test-category',
                max_cloud_cover=42,
                name='test-name',
                spatial_filter_id='test-spatial-filter-id',
                start_on=DATE_START,
                stop_on=DATE_STOP,
                user_id='test-user-id',
            )


@patch('bfapi.db.productlines.select_all')
class GetAllTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.productlines')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_returns_list_of_productlines(self, mock: MagicMock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        records = productlines.get_all()
        self.assertIsInstance(records, list)
        self.assertIsInstance(records[0], productlines.ProductLine)

    def test_assigns_correct_productline_id(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual('test-productline-id', record.productline_id)

    def test_assigns_correct_algorithm_name(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        records = productlines.get_all()
        self.assertEqual('test-algo-name', records[0].algorithm_name)

    def test_assigns_correct_bbox(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual({"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
                         record.bbox)

    def test_assigns_correct_category(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual('test-category', record.category)

    def test_assigns_correct_created_by(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual('test-created-by', record.created_by)

    def test_assigns_correct_created_on(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual(datetime.utcnow().date(), record.created_on.date())

    def test_assigns_correct_max_cloud_cover(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual(42, record.max_cloud_cover)

    def test_assigns_correct_name(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual('test-name', record.name)

    def test_assigns_correct_owner(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual('test-productline-owner', record.owned_by)

    def test_assigns_correct_spatial_filter_id(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual('test-spatial-filter-id', record.spatial_filter_id)

    def test_assigns_correct_start_date(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual(DATE_START, record.start_on)

    def test_assigns_correct_stop_date(self, mock):
        mock.return_value.fetchall.return_value = [create_productline_db_record()]
        record = productlines.get_all().pop()
        self.assertEqual(DATE_STOP, record.stop_on)

    def test_can_handle_multiple_records(self, mock: MagicMock):
        mock.return_value.fetchall.return_value = [
            create_productline_db_record('record1'),
            create_productline_db_record('record2'),
        ]
        records = productlines.get_all()
        self.assertEqual(['record1', 'record2'], list(map(lambda p: p.productline_id, records)))

    def test_can_handle_empty_recordset(self, mock: MagicMock):
        mock.return_value.fetchall.return_value = []
        self.assertEqual([], productlines.get_all())

    def test_gracefully_handles_db_errors(self, mock: MagicMock):
        mock.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            productlines.get_all()


class HandleHarvestEventTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.productlines')
        self._logger.disabled = True

        self.mock_create_job = self.create_mock('bfapi.service.jobs.create')
        self.mock_insert_pljob = self.create_mock('bfapi.db.productlines.insert_productline_job')
        self.mock_select_jobs = self.create_mock('bfapi.db.jobs.select_jobs_for_inputs')
        self.mock_select_pls = self.create_mock('bfapi.db.productlines.select_summary_for_scene')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_passes_correct_cloudcover_to_productline_query(self):
        self.mock_select_pls.return_value.fetchall.return_value = [create_productline_db_summary()]
        productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        )
        self.assertEqual(40, self.mock_select_pls.call_args[1]['cloud_cover'])

    def test_passes_correct_bbox_to_productline_query(self):
        self.mock_select_pls.return_value.fetchall.return_value = [create_productline_db_summary()]
        productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        )
        self.assertEqual(0, self.mock_select_pls.call_args[1]['min_x'])
        self.assertEqual(0, self.mock_select_pls.call_args[1]['min_y'])
        self.assertEqual(30, self.mock_select_pls.call_args[1]['max_x'])
        self.assertEqual(30, self.mock_select_pls.call_args[1]['max_y'])

    def test_returns_correct_disposition_when_productline_found(self):
        self.mock_select_pls.return_value.fetchall.return_value = [create_productline_db_summary()]
        self.assertEqual('Accept', productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        ))

    def test_returns_correct_disposition_when_productline_is_not_found(self):
        self.mock_select_pls.return_value.fetchall.return_value = []
        self.assertEqual('Disregard', productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        ))

    def test_can_handle_multiple_applicable_productlines(self):
        self.mock_select_pls.return_value.fetchall.return_value = [
            create_productline_db_summary(),
            create_productline_db_summary(),
            create_productline_db_summary(),
        ]
        self.assertEqual('Accept', productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        ))

    def test_throws_if_signature_is_invalid(self):
        with self.assertRaises(productlines.UntrustedEventError):
            productlines.handle_harvest_event(
                scene_id='test-scene-id',
                signature='0123456789abcdef' * 6,
                cloud_cover=40,
                min_x=0,
                min_y=0,
                max_x=30,
                max_y=30,
            )

    def test_creates_job_if_scene_not_already_processed(self):
        self.mock_select_pls.return_value.fetchall.return_value = [create_productline_db_summary()]
        self.mock_select_jobs.return_value.scalar.return_value = None
        productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        )
        self.assertTrue(self.mock_create_job.called)

    def test_does_not_create_job_if_scene_already_processed(self):
        self.mock_select_pls.return_value.fetchall.return_value = [create_productline_db_summary()]
        self.mock_select_jobs.return_value.scalar.return_value = 'test-existing-job-id'
        productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        )
        self.assertFalse(self.mock_create_job.called)

    def test_calls_create_job_with_correct_inputs(self):
        self.mock_select_pls.return_value.fetchall.return_value = [create_productline_db_summary()]
        self.mock_select_jobs.return_value.scalar.return_value = None
        productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        )
        self.assertEqual({
            'api_key': None,
            'user_id': 'test-productline-owner',
            'scene_id': 'test-scene-id',
            'service_id': 'test-algo-id',
            'job_name': 'TEST_NAME/TEST-SCENE-ID',
        }, self.mock_create_job.call_args[1])

    def test_links_spawned_jobs_to_productline(self):
        self.mock_select_pls.return_value.fetchall.return_value = [create_productline_db_summary()]
        self.mock_select_jobs.return_value.scalar.return_value = None
        self.mock_create_job.return_value = create_job(job_id='test-new-job-id')
        productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        )
        self.assertEqual({
            'job_id': 'test-new-job-id',
            'productline_id': 'test-productline-id',
        }, self.mock_insert_pljob.call_args[1])

    def test_links_existing_jobs_to_productline(self):
        self.mock_select_pls.return_value.fetchall.return_value = [create_productline_db_summary()]
        self.mock_select_jobs.return_value.scalar.return_value = 'test-existing-job-id'
        productlines.handle_harvest_event(
            scene_id='test-scene-id',
            signature=SIGNATURE,
            cloud_cover=40,
            min_x=0,
            min_y=0,
            max_x=30,
            max_y=30,
        )
        self.assertEqual({
            'job_id': 'test-existing-job-id',
            'productline_id': 'test-productline-id',
        }, self.mock_insert_pljob.call_args[1])


class InstallIfNeededTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.productlines')
        self._logger.disabled = True

        self.mock_get_etid = self.create_mock('bfapi.service.scenes.get_event_type_id')
        self.mock_get_etid.return_value = 'test-event-type-id'
        self.mock_create_trigger = self.create_mock('bfapi.piazza.create_trigger')
        self.mock_get_triggers = self.create_mock('bfapi.piazza.get_triggers')
        self.mock_register_service = self.create_mock('bfapi.piazza.register_service')
        self.mock_get_services = self.create_mock('bfapi.piazza.get_services')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_searches_piazza_for_harvest_event_handler(self):
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual({'pattern': '^beachfront:api:on_harvest_event$'}, self.mock_get_services.call_args[1])

    def test_does_not_register_new_handler_if_one_exists(self):
        self.mock_get_services.return_value = [{}]
        productlines.install_if_needed('/test/endpoint')
        self.assertFalse(self.mock_register_service.called)

    def test_registers_handler_if_not_found(self):
        self.mock_get_services.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertTrue(self.mock_register_service.called)

    def test_registers_handler_with_correct_contract_url(self):
        self.mock_get_services.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual('https://bf-api.localhost', self.mock_register_service.call_args[1]['contract_url'])

    def test_registers_handler_with_correct_description(self):
        self.mock_get_services.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual('Beachfront handler for Scene Harvest Event', self.mock_register_service.call_args[1]['description'])

    def test_registers_handler_with_correct_name(self):
        self.mock_get_services.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual('beachfront:api:on_harvest_event', self.mock_register_service.call_args[1]['name'])

    def test_registers_handler_with_correct_url(self):
        self.mock_get_services.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual('https://bf-api.localhost/test/endpoint', self.mock_register_service.call_args[1]['url'])

    def test_searches_piazza_for_harvest_event_trigger(self):
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual('beachfront:api:on_harvest_event', self.mock_get_triggers.call_args[0][1])

    def test_does_not_register_new_trigger_if_one_exists(self):
        self.mock_get_triggers.return_value = [create_service()]
        productlines.install_if_needed('/test/endpoint')
        self.assertFalse(self.mock_create_trigger.called)

    def test_creates_trigger_if_not_found(self):
        self.mock_get_triggers.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertTrue(self.mock_create_trigger.called)

    def test_requests_event_type_id_from_catalog(self):
        self.mock_get_triggers.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertTrue(self.mock_get_etid.called)

    def test_creates_trigger_with_correct_data_inputs(self):
        self.mock_get_triggers.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual({
            "body": {
                "content": """{
                            "__signature__": "%s",
                            "scene_id": "$imageID",
                            "captured_on": "$acquiredDate",
                            "cloud_cover": $cloudCover,
                            "min_x": $minx,
                            "min_y": $miny,
                            "max_x": $maxx,
                            "max_y": $maxy
                        }""" % SIGNATURE,
                "type": "body",
                "mimeType": "application/json",
            },
        }, self.mock_create_trigger.call_args[1]['data_inputs'])

    def test_creates_trigger_with_correct_event_type_id(self):
        self.mock_get_triggers.return_value = []
        self.mock_get_etid.return_value = 'test-event-type-id'
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual('test-event-type-id', self.mock_create_trigger.call_args[1]['event_type_id'])

    def test_creates_trigger_with_correct_name(self):
        self.mock_get_triggers.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual('beachfront:api:on_harvest_event', self.mock_create_trigger.call_args[1]['name'])

    def test_creates_trigger_with_correct_service_id(self):
        self.mock_get_services.return_value = [create_service()]
        self.mock_get_triggers.return_value = []
        productlines.install_if_needed('/test/endpoint')
        self.assertEqual('test-service-id', self.mock_create_trigger.call_args[1]['service_id'])

    def test_throws_when_piazza_throws(self):
        self.mock_get_services.side_effect = piazza.Unauthorized()
        with self.assertRaises(piazza.Unauthorized):
            productlines.install_if_needed('/test/endpoint')


#
# Helpers
#

def create_algorithm():
    return Algorithm(
        bands=('test-algo-band-1', 'test-algo-band-2'),
        description='test-algo-description',
        interface='test-algo-interface',
        max_cloud_cover=42,
        name='test-algo-name',
        service_id='test-algo-id',
        url='test-algo-url',
        version='test-algo-version',
    )


def create_job(job_id: str = 'test-job-id'):
    return Job(
        algorithm_name='test-algo-name',
        algorithm_version='test-algo-version',
        created_by='test-created-by',
        created_on=datetime.utcnow(),
        geometry={},
        job_id=job_id,
        name='test-job-name',
        scene_capture_date=datetime.utcnow(),
        scene_sensor_name='test-scene-sensor-name',
        scene_id='test-scene-id',
        status='test-status',
        tide=5.4321,
        tide_min_24h=-10.0,
        tide_max_24h=10.0,
    )


def create_service():
    return piazza.ServiceDescriptor(
        description='test-description',
        metadata={},
        name='test-name',
        service_id='test-service-id',
        url='test-url',
    )


def create_productline_db_record(record_id: str = 'test-productline-id'):
    return {
        'productline_id': record_id,
        'algorithm_name': 'test-algo-name',
        'bbox': '{"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]}',
        'category': 'test-category',
        'created_by': 'test-created-by',
        'created_on': datetime.utcnow(),
        'max_cloud_cover': 42,
        'name': 'test-name',
        'owned_by': 'test-productline-owner',
        'spatial_filter_id': 'test-spatial-filter-id',
        'start_on': DATE_START,
        'stop_on': DATE_STOP,
    }


def create_productline_db_summary():
    return {
        'productline_id': 'test-productline-id',
        'algorithm_id': 'test-algo-id',
        'name': 'test-name',
        'owned_by': 'test-productline-owner',
    }
