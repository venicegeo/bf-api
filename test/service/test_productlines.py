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
from datetime import datetime
from unittest.mock import patch, MagicMock

from test import helpers

from bfapi.db import DatabaseError
from bfapi.service import productlines
from bfapi.service.algorithms import Algorithm, NotFound, ValidationError

DATE_START = datetime.utcfromtimestamp(1400000000)
DATE_STOP = datetime.utcfromtimestamp(1500000000)


@patch('bfapi.service.algorithms.get')
class CreateProductlineTest(unittest.TestCase):
    maxDiff = 1024

    def setUp(self):
        self._mockdb = helpers.mock_database()

    def tearDown(self):
        self._mockdb.destroy()

    def test_returns_productline(self, _):
        record = productlines.create_productline(
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
        mock.assert_called_with('test-algo-id')

    def test_gracefully_handles_algorithm_not_found(self, mock: MagicMock):
        mock.side_effect = NotFound('test-algo-id')
        with self.assertRaisesRegex(NotFound, 'algorithm `test-algo-id` does not exist'):
            productlines.create_productline(
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


class DeleteProductLineTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()

        self.mock_delete = self.create_mock('bfapi.db.productlines.delete_productline')
        self.mock_select = self.create_mock('bfapi.db.productlines.select_productline')

    def tearDown(self):
        self._mockdb.destroy()

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_deletes_productline_from_database(self):
        self.mock_select.return_value.fetchone.return_value = {'owned_by': 'test-user-id'}
        productlines.delete_productline('test-user-id', 'test-productline-id')
        self.assertEqual(1, self.mock_delete.call_count)

    def test_closes_connection_after_operation(self):
        self.mock_select.return_value.fetchone.return_value = {'owned_by': 'test-user-id'}
        productlines.delete_productline('test-user-id', 'test-productline-id')
        self.assertEqual(1, self._mockdb.close.call_count)

    def test_throws_when_productline_not_found(self):
        self.mock_select.return_value.fetchone.return_value = None
        with self.assertRaises(productlines.NotFound):
            productlines.delete_productline('test-user-id', 'test-productline-id')

    def test_throws_when_not_owned_by_requesting_user(self):
        self.mock_select.return_value.fetchone.return_value = {'owned_by': 'Rumplestiltzkin'}
        with self.assertRaises(PermissionError):
            productlines.delete_productline('person who is not Rumplestiltzkin', 'test-productline-id')

    def test_throws_on_database_error_during_select(self):
        self.mock_select.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            productlines.delete_productline('test-user-id', 'test-productline-id')

    def test_throws_on_database_error_during_delete(self):
        self.mock_select.return_value.fetchone.return_value = {'owned_by': 'test-user-id'}
        self.mock_delete.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            productlines.delete_productline('test-user-id', 'test-productline-id')


@patch('bfapi.db.productlines.select_all')
class GetAllTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()

    def tearDown(self):
        self._mockdb.destroy()

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


#
# Helpers
#

def create_algorithm():
    return Algorithm(
        description='test-algo-description',
        interface='test-algo-interface',
        max_cloud_cover=42,
        name='test-algo-name',
        service_id='test-algo-id',
        version='test-algo-version',
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
