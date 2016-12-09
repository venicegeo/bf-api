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

import io
import json
import logging
import unittest
from datetime import datetime, timedelta
from unittest.mock import call, patch, Mock

import requests
import requests_mock as rm

from test import helpers

import bfapi.service.algorithms
import bfapi.service.scenes
from bfapi import piazza
from bfapi.db import DatabaseError
from bfapi.service import jobs

API_KEY = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
LAST_WEEK = datetime.utcnow() - timedelta(7.0)


class CreateJobTest(unittest.TestCase):
    maxDiff = 4096

    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs')
        self._logger.disabled = True

        self.mock_requests = rm.Mocker()  # type: rm.Mocker
        self.mock_requests.start()
        self.addCleanup(self.mock_requests.stop)
        self.mock_execute = self.create_mock('bfapi.piazza.execute')
        self.mock_get_scene = self.create_mock('bfapi.service.scenes.get')
        self.mock_get_algo = self.create_mock('bfapi.service.algorithms.get')
        self.mock_insert_job = self.create_mock('bfapi.db.jobs.insert_job')
        self.mock_insert_job_user = self.create_mock('bfapi.db.jobs.insert_job_user')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def create_logstream(self) -> io.StringIO:
        def cleanup():
            self._logger.propagate = True

        self._logger.propagate = False
        self._logger.disabled = False
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self._logger.addHandler(handler)
        self.addCleanup(cleanup)
        return stream

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_returns_job(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)

    def test_assigns_correct_algorithm_name(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-algo-name', job.algorithm_name)

    def test_assigns_correct_algorithm_version(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-algo-version', job.algorithm_version)

    def test_assigns_correct_created_by(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-user-id', job.created_by)

    def test_assigns_correct_created_on(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual(datetime.utcnow().date(), job.created_on.date())

    def test_assigns_correct_geometry(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual({"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
                         job.geometry)

    def test_assigns_correct_job_id(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        self.mock_execute.return_value = 'test-new-job-id'
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-new-job-id', job.job_id)

    def test_assigns_correct_name(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-name', job.name)

    def test_assigns_correct_scene_capture_date(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('2014-05-13T16:53:20', job.scene_capture_date.isoformat())

    def test_assigns_correct_scene_sensor_name(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-sensor-name', job.scene_sensor_name)

    def test_assigns_correct_scene_id(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-scene-id', job.scene_id)

    def test_assigns_correct_status(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        job = jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('Submitted', job.status)

    def test_requests_tide_prediction(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertEqual('https://bf-tideprediction.localhost/tides', self.mock_requests.request_history[0].url)
        self.assertEqual({
            'locations': [{
                'lat': 15.0,
                'lon': 15.0,
                'dtg': '2014-05-13-16-53',
            }]
        }, self.mock_requests.request_history[0].json())

    def test_fetches_correct_scene(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertEqual(call('test-scene-id'), self.mock_get_scene.call_args)

    def test_sends_correct_payload_to_piazza(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertEqual(API_KEY, self.mock_execute.call_args[0][0])
        self.assertEqual('test-algo-id', self.mock_execute.call_args[0][1])
        self.assertEqual({
            'pzAuthKey': 'Basic YWFhYWFhYWEtYmJiYi1jY2NjLWRkZGQtZWVlZWVlZWVlZWVlOg==',
            'cmd': 'shoreline' +
                   ' --image test-algo-band-1.TIF,test-algo-band-2.TIF' +
                   ' --projection geo-scaled' +
                   ' --threshold 0.5' +
                   ' --tolerance 0.075' +
                   ' --prop tide:2.6171416114' +
                   ' --prop tide_min_24h:2.6171416114' +
                   ' --prop tide_max_24h:2.512895346998' +
                   ' --prop classification:Unclassified' +
                   ' --prop data_usage:NOT_TO_BE_USED_FOR_NAVIGATIONAL_OR_TARGETING_PURPOSES' +
                   ' shoreline.geojson',
            'inExtFiles': ['lorem', 'ipsum'],
            'inExtNames': ['test-algo-band-1.TIF', 'test-algo-band-2.TIF'],
            'outGeoJson': ['shoreline.geojson'],
        }, json.loads(self.mock_execute.call_args[0][2]['body']['content']))

    def test_discards_invalid_tide_predictions(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE_NIL)
        jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertEqual('shoreline' +
                         ' --image test-algo-band-1.TIF,test-algo-band-2.TIF' +
                         ' --projection geo-scaled' +
                         ' --threshold 0.5' +
                         ' --tolerance 0.075' +
                         ' --prop tide:nil' +
                         ' --prop tide_min_24h:nil' +
                         ' --prop tide_max_24h:nil' +
                         ' --prop classification:Unclassified' +
                         ' --prop data_usage:NOT_TO_BE_USED_FOR_NAVIGATIONAL_OR_TARGETING_PURPOSES' +
                         ' shoreline.geojson',
                         json.loads(self.mock_execute.call_args[0][2]['body']['content'])['cmd'])

    def test_does_not_create_database_record_if_cannot_start(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE_NIL)
        self.mock_execute.side_effect = piazza.ServerError(500)
        try:
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        except:
            pass
        self.assertEqual(0, self.mock_insert_job.call_count)
        self.assertEqual(0, self.mock_insert_job_user.call_count)

    def test_logs_creation_success(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        logstream = self.create_logstream()
        jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-service-id', 'test-name')
        self.assertEqual([
            'INFO - Dispatching <scene:test-scene-id> to <algo:test-algo-name>',
        ], logstream.getvalue().splitlines())

    def test_logs_creation_failure_during_algorithm_retrieval(self):
        self.mock_get_algo.side_effect = bfapi.service.algorithms.NotFound('test-algo-id')
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        logstream = self.create_logstream()
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')
        self.assertEqual([
            'ERROR - Preprocessing error: algorithm `test-algo-id` does not exist',
        ], logstream.getvalue().splitlines())

    def test_logs_creation_failure_during_scene_retrieval(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.side_effect = bfapi.service.scenes.NotFound('test-scene-id')
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        logstream = self.create_logstream()
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')
        self.assertEqual([
            'ERROR - Preprocessing error: scene `test-scene-id` not found in catalog',
        ], logstream.getvalue().splitlines())

    def test_logs_creation_failure_during_tide_prediction(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text='oh noes', status_code=502)
        logstream = self.create_logstream()
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')
        self.assertEqual([
            'ERROR - Preprocessing error: tide prediction failed: HTTP 502',
        ], logstream.getvalue().splitlines())

    def test_discards_malformed_tide_service_response(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text='lolwut')
        logstream = self.create_logstream()
        jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')
        self.assertEqual([
            'ERROR - Malformed tide prediction response:',
            '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',
            '',
            'INPUTS',
            '',
            '    dtg: 2014-05-13-16-53',
            '    lat: 15.0',
            '    lon: 15.0',
            '',
            'RESPONSE',
            '',
            'lolwut',
            '',
            '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',
            'INFO - Dispatching <scene:test-scene-id> to <algo:test-algo-name>',
        ], logstream.getvalue().splitlines())

    def test_logs_creation_failure_during_execution(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        self.mock_execute.side_effect = piazza.ServerError(400)
        logstream = self.create_logstream()
        with self.assertRaises(piazza.ServerError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')
        self.assertEqual([
            'INFO - Dispatching <scene:test-scene-id> to <algo:test-algo-name>',
            'ERROR - Could not execute via Piazza: Piazza server error (HTTP 400)'
        ], logstream.getvalue().splitlines())

    def test_logs_creation_failure_during_database_insert(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        self.mock_insert_job.side_effect = helpers.create_database_error()
        logstream = self.create_logstream()
        with self.assertRaises(DatabaseError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')
        self.assertEqual([
            'INFO - Dispatching <scene:test-scene-id> to <algo:test-algo-name>',
            "ERROR - Could not save job to database: (builtins.Exception) test-error [SQL: 'test-query']",
        ], logstream.getvalue().splitlines())

    def test_throws_when_piazza_throws(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        self.mock_execute.side_effect = piazza.ServerError(500)
        with self.assertRaises(piazza.ServerError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')

    def test_throws_when_database_insertion_fails(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        self.mock_insert_job.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')

    def test_throws_when_algorithm_not_found(self):
        self.mock_get_algo.side_effect = bfapi.service.algorithms.NotFound('test-algo-id')
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')

    def test_throws_when_scene_not_found(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.side_effect = bfapi.service.scenes.NotFound('test-scene-id')
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')

    def test_throws_when_scene_is_missing_required_bands(self):
        self.mock_get_algo.return_value = create_algorithm()
        scene = create_scene()
        scene.bands.pop('test-algo-band-1')
        self.mock_get_scene.return_value = scene
        # self.mock_requests.post('/tides', text=RESPONSE_TIDE)
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')

    def test_throws_when_catalog_is_unreachable(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.side_effect = bfapi.service.scenes.CatalogError()
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')

    def test_throws_when_tide_service_is_unreachable(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        with patch('requests.post') as mock:
            mock.side_effect = requests.ConnectionError()
            with self.assertRaises(jobs.PreprocessingError):
                jobs.create(API_KEY, 'test-user-id', 'test-scene-id', 'test-algo-id', 'test-name')


@patch('bfapi.db.jobs.delete_job_user')
@patch('bfapi.db.jobs.exists')
class ForgetJobTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_deletes_job_user_record(self, _, mock_delete: Mock):
        jobs.forget('test-user-id', 'test-job-id')
        self.assertTrue(mock_delete.called)

    def test_passes_correct_params(self, _, mock_delete: Mock):
        jobs.forget('test-user-id', 'test-job-id')
        self.assertEqual({'user_id': 'test-user-id', 'job_id': 'test-job-id'}, mock_delete.call_args[1])

    def test_throws_if_job_not_found(self, mock_exists: Mock, _):
        mock_exists.return_value = False
        with self.assertRaises(jobs.NotFound):
            jobs.forget('test-user-id', 'test-job-id')

    def test_throws_if_delete_failed(self, _, mock_delete: Mock):
        mock_delete.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            jobs.forget('test-user-id', 'test-job-id')


@patch('bfapi.db.jobs.select_jobs_for_user')
class GetAllJobsTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_returns_a_list_of_jobs(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        records = jobs.get_all('test-user-id')
        self.assertIsInstance(records, list)
        self.assertEqual(1, len(records))
        self.assertIsInstance(records[0], jobs.Job)

    def test_queries_on_correct_userid(self, mock: Mock):
        mock.return_value.fetchall.return_value = []
        jobs.get_all('test-user-id')
        self.assertEqual({'user_id': 'test-user-id'}, mock.call_args[1])

    def test_can_handle_empty_recordset(self, mock: Mock):
        mock.return_value.fetchall.return_value = []
        records = jobs.get_all('test-user-id')
        self.assertEqual([], records)

    def test_can_handle_multiple_records(self, mock: Mock):
        mock.return_value.fetchall.return_value = [
            create_job_db_record('test-job-1'),
            create_job_db_record('test-job-2'),
            create_job_db_record('test-job-3'),
        ]
        records = jobs.get_all('test-user-id')
        self.assertEqual(['test-job-1', 'test-job-2', 'test-job-3'], list(map(lambda r: r.job_id, records)))

    def test_assigns_correct_algorithm_name(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual('test-algo-name', job.algorithm_name)

    def test_assigns_correct_algorithm_version(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual('test-algo-version', job.algorithm_version)

    def test_assigns_correct_created_by(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual('test-creator', job.created_by)

    def test_assigns_correct_created_on(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual(datetime.utcnow().date(), job.created_on.date())

    def test_assigns_correct_geometry(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual({"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
                         job.geometry)

    def test_assigns_correct_job_id(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual('test-job-id', job.job_id)

    def test_assigns_correct_name(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual('test-name', job.name)

    def test_assigns_correct_scene_capture_date(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual(datetime.utcnow().date(), job.scene_capture_date.date())

    def test_assigns_correct_scene_sensor_name(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual('test-scene-sensor-name', job.scene_sensor_name)

    def test_assigns_correct_scene_id(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual('test-scene-id', job.scene_id)

    def test_assigns_correct_status(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual('test-status', job.status)

    def test_assigns_correct_tide(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual(5.4321, job.tide)

    def test_assigns_correct_tide_min_24h(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual(-10.0, job.tide_min_24h)

    def test_assigns_correct_tide_max_24h(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual(10.0, job.tide_max_24h)

    def test_handles_database_errors_gracefully(self, mock: Mock):
        mock.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            jobs.get_all('test-user-id')


@patch('bfapi.db.jobs.select_detections')
@patch('bfapi.db.jobs.exists', return_value=True)
class GetDetectionsTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_returns_a_stringified_feature_collection(self, _, mock_select_detections: Mock):
        mock_select_detections.return_value.scalar.return_value = '{"type":"FeatureCollection","features":[]}'
        detections = jobs.get_detections('test-job-id')
        self.assertEqual('{"type":"FeatureCollection","features":[]}', detections)

    def test_queries_on_correct_jobid(self, mock_exists: Mock, mock_select_detections: Mock):
        mock_select_detections.return_value.scalar.return_value = '{"type":"FeatureCollection","features":[]}'
        jobs.get_detections('test-job-id')
        self.assertEqual({'job_id': 'test-job-id'}, mock_exists.call_args[1])

    def test_can_handle_big_feature_collections(self, _, mock_select_detections: Mock):
        some_huge_number = 1024 * 100000
        mock_select_detections.return_value.scalar.return_value = 'x' * some_huge_number
        detections = jobs.get_detections('test-job-id')
        self.assertEqual(some_huge_number, len(detections))

    def test_handles_database_errors_gracefully(self, _, mock_select_detections: Mock):
        mock_select_detections.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            jobs.get_detections('test-job-id')

    def test_handles_database_errors_gracefully_during_existence_check(self, mock_exists: Mock, _):
        mock_exists.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            jobs.get_detections('test-job-id')

    def test_throws_if_job_not_found(self, mock_exists: Mock, _):
        mock_exists.return_value = False
        with self.assertRaises(jobs.NotFound):
            jobs.get_detections('test-job-id')


@patch('bfapi.db.jobs.insert_job_user')
@patch('bfapi.db.jobs.select_job')
class GetJobTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_returns_job(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        self.assertIsInstance(jobs.get('test-user-id', 'test-job-id'), jobs.Job)

    def test_throws_if_job_not_found(self, mock_select: Mock, _):
        with self.assertRaises(jobs.NotFound):
            mock_select.return_value.fetchone.return_value = None
            jobs.get('test-user-id', 'test-job-id')

    def test_queries_on_correct_ids(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        jobs.get('test-user-id', 'test-job-id')
        self.assertEqual(call(self._mockdb, job_id='test-job-id'), mock_select.call_args)

    def test_assigns_correct_algorithm_name(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual('test-algo-name', job.algorithm_name)

    def test_assigns_correct_algorithm_version(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual('test-algo-version', job.algorithm_version)

    def test_assigns_correct_created_by(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual('test-creator', job.created_by)

    def test_assigns_correct_created_on(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual(datetime.utcnow().date(), job.created_on.date())

    def test_assigns_correct_geometry(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual({"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
                         job.geometry)

    def test_assigns_correct_job_id(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual('test-job-id', job.job_id)

    def test_assigns_correct_name(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual('test-name', job.name)

    def test_assigns_correct_scene_capture_date(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual(datetime.utcnow().date(), job.scene_capture_date.date())

    def test_assigns_correct_scene_sensor_name(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual('test-scene-sensor-name', job.scene_sensor_name)

    def test_assigns_correct_scene_id(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual('test-scene-id', job.scene_id)

    def test_assigns_correct_status(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual('test-status', job.status)

    def test_assigns_correct_tide(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual(5.4321, job.tide)

    def test_assigns_correct_tide_min_24h(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual(-10.0, job.tide_min_24h)

    def test_assigns_correct_tide_max_24h(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual(10.0, job.tide_max_24h)

    def test_adds_job_to_user_tracker(self, mock_select: Mock, mock_insert: Mock):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        jobs.get('test-user-id', 'test-job-id')
        self.assertEqual({'job_id': 'test-job-id', 'user_id': 'test-user-id'}, mock_insert.call_args[1])


@patch('bfapi.db.jobs.select_jobs_for_productline')
class GetByProductlineTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_returns_a_list_of_jobs(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        records = jobs.get_by_productline('test-productline-id', LAST_WEEK)
        self.assertIsInstance(records, list)
        self.assertEqual(1, len(records))
        self.assertIsInstance(records[0], jobs.Job)

    def test_queries_on_correct_plid(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        jobs.get_by_productline('test-productline-id', LAST_WEEK)
        self.assertEqual('test-productline-id', mock.call_args[1]['productline_id'])

    def test_queries_on_correct_since_timestamp(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        jobs.get_by_productline('test-productline-id', datetime.utcfromtimestamp(1234567890))
        self.assertEqual(datetime.utcfromtimestamp(1234567890), mock.call_args[1]['since'])

    def test_can_handle_empty_recordset(self, mock: Mock):
        mock.return_value.fetchall.return_value = []
        records = jobs.get_by_productline('test-productline-id', LAST_WEEK)
        self.assertEqual([], records)

    def test_can_handle_multiple_records(self, mock: Mock):
        mock.return_value.fetchall.return_value = [
            create_job_db_record('test-job-1'),
            create_job_db_record('test-job-2'),
            create_job_db_record('test-job-3'),
        ]
        records = jobs.get_by_productline('test-productline-id', LAST_WEEK)
        self.assertEqual(['test-job-1', 'test-job-2', 'test-job-3'], list(map(lambda r: r.job_id, records)))

    def test_assigns_correct_algorithm_name(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual('test-algo-name', job.algorithm_name)

    def test_assigns_correct_algorithm_version(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual('test-algo-version', job.algorithm_version)

    def test_assigns_correct_created_by(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual('test-creator', job.created_by)

    def test_assigns_correct_created_on(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual(datetime.utcnow().date(), job.created_on.date())

    def test_assigns_correct_geometry(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual({"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
                         job.geometry)

    def test_assigns_correct_job_id(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual('test-job-id', job.job_id)

    def test_assigns_correct_name(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual('test-name', job.name)

    def test_assigns_correct_scene_capture_date(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual(datetime.utcnow().date(), job.scene_capture_date.date())

    def test_assigns_correct_scene_sensor_name(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual('test-scene-sensor-name', job.scene_sensor_name)

    def test_assigns_correct_scene_id(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual('test-scene-id', job.scene_id)

    def test_assigns_correct_status(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual('test-status', job.status)

    def test_assigns_correct_tide(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual(5.4321, job.tide)

    def test_assigns_correct_tide_min_24h(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual(-10.0, job.tide_min_24h)

    def test_assigns_correct_tide_max_24h(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual(10.0, job.tide_max_24h)

    def test_handles_database_errors_gracefully(self, mock: Mock):
        mock.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            jobs.get_by_productline('test-productline-id', LAST_WEEK)


@patch('bfapi.db.jobs.select_jobs_for_scene')
class GetBySceneTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_returns_a_list_of_jobs(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        records = jobs.get_by_scene('test-scene-id')
        self.assertIsInstance(records, list)
        self.assertEqual(1, len(records))
        self.assertIsInstance(records[0], jobs.Job)

    def test_queries_on_correct_scene_id(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        jobs.get_by_scene('test-scene-id')
        self.assertEqual({'scene_id': 'test-scene-id'}, mock.call_args[1])

    def test_can_handle_empty_recordset(self, mock: Mock):
        mock.return_value.fetchall.return_value = []
        records = jobs.get_by_scene('test-scene-id')
        self.assertEqual([], records)

    def test_can_handle_multiple_records(self, mock: Mock):
        mock.return_value.fetchall.return_value = [
            create_job_db_record('test-job-1'),
            create_job_db_record('test-job-2'),
            create_job_db_record('test-job-3'),
        ]
        records = jobs.get_by_scene('test-scene-id')
        self.assertEqual(['test-job-1', 'test-job-2', 'test-job-3'], list(map(lambda r: r.job_id, records)))

    def test_assigns_correct_algorithm_name(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual('test-algo-name', job.algorithm_name)

    def test_assigns_correct_algorithm_version(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual('test-algo-version', job.algorithm_version)

    def test_assigns_correct_created_by(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual('test-creator', job.created_by)

    def test_assigns_correct_created_on(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual(datetime.utcnow().date(), job.created_on.date())

    def test_assigns_correct_geometry(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual({"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
                         job.geometry)

    def test_assigns_correct_job_id(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual('test-job-id', job.job_id)

    def test_assigns_correct_name(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual('test-name', job.name)

    def test_assigns_correct_scene_capture_date(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual(datetime.utcnow().date(), job.scene_capture_date.date())

    def test_assigns_correct_scene_sensor_name(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual('test-scene-sensor-name', job.scene_sensor_name)

    def test_assigns_correct_scene_id(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual('test-scene-id', job.scene_id)

    def test_assigns_correct_status(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual('test-status', job.status)

    def test_assigns_correct_tide(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual(5.4321, job.tide)

    def test_assigns_correct_tide_min_24h(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual(-10.0, job.tide_min_24h)

    def test_assigns_correct_tide_max_24h(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual(10.0, job.tide_max_24h)

    def test_handles_database_errors_gracefully(self, mock: Mock):
        mock.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            jobs.get_by_scene('test-scene-id')


@patch('bfapi.service.jobs.Worker')
class StartWorkerTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs')
        self._logger.disabled = True

    def tearDown(self):
        jobs.stop_worker()
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_module_does_not_start_worker_until_invoked(self, _):
        self.assertIsNone(jobs._worker)

    def test_starts_worker(self, _):
        jobs.start_worker()
        self.assertEqual(1, jobs._worker.start.call_count)

    def test_retains_worker_instance(self, _):
        jobs.start_worker()
        self.assertIsNotNone(jobs._worker)

    def test_passes_correct_params_to_worker(self, mock: Mock):
        jobs.start_worker(
            api_key='test-api-key',
            job_ttl=timedelta(12),
            interval=timedelta(34),
        )
        self.assertEqual(('test-api-key', timedelta(12), timedelta(34)), mock.call_args[0])

    def test_throws_if_worker_already_exists(self, _):
        jobs.start_worker()
        with self.assertRaisesRegex(jobs.Error, 'worker already started'):
            jobs.start_worker()


@patch('bfapi.service.jobs.Worker')
class StopWorkerTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_stops_worker(self, _):
        jobs.start_worker()
        stub = jobs._worker.terminate
        jobs.stop_worker()
        self.assertIsNone(jobs._worker)
        self.assertEqual(1, stub.call_count)

    def test_can_handle_gratuitous_invocations(self, _):
        jobs.start_worker()
        jobs.stop_worker()
        jobs.stop_worker()
        jobs.stop_worker()

    def test_does_not_throw_if_worker_not_started(self, _):
        jobs.stop_worker()


class WorkerRunTest(unittest.TestCase):
    maxDiff = 4096

    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.jobs.worker')
        self._logger.disabled = True
        self._logger_for_module = logging.getLogger('bfapi.service.jobs')
        self._logger_for_module.disabled = True

        self.mock_sleep = self.create_mock('time.sleep')
        self.mock_thread = self.create_mock('threading.Thread')
        self.mock_getfile = self.create_mock('bfapi.piazza.get_file')
        self.mock_getstatus = self.create_mock('bfapi.piazza.get_status')
        self.mock_insert_detections = self.create_mock('bfapi.db.jobs.insert_detection')
        self.mock_select_jobs = self.create_mock('bfapi.db.jobs.select_outstanding_jobs')
        self.mock_select_jobs.return_value.fetchall.return_value = []
        self.mock_update_status = self.create_mock('bfapi.db.jobs.update_status')
        self.mock_insert_job_failure = self.create_mock('bfapi.db.jobs.insert_job_failure')

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False
        self._logger_for_module.disabled = False

    def create_logstream(self) -> io.StringIO:
        def cleanup():
            self._logger.propagate = True

        self._logger.propagate = False
        self._logger.disabled = False
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self._logger.addHandler(handler)
        self.addCleanup(cleanup)
        return stream

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def create_worker(self, *, max_cycles=1, interval=timedelta(1)):
        worker = jobs.Worker('test-api-key', job_ttl=timedelta(1), interval=interval)
        values = (v for v in [*[False] * max_cycles, True])
        worker.is_terminated = lambda: next(values)
        return worker

    def test_requests_list_of_outstanding_jobs(self):
        worker = self.create_worker()
        worker.run()
        self.assertEqual(1, self.mock_select_jobs.call_count)

    def test_closes_database_connection_after_each_cycle(self):
        worker = self.create_worker(max_cycles=13)
        worker.run()
        self.assertEqual(13, self._mockdb.close.call_count)

    def test_runs_first_cycle_immediately(self):
        worker = self.create_worker()
        worker.run()
        self.assertEqual(1, self.mock_select_jobs.call_count)
        self.assertEqual(1, self.mock_sleep.call_count)

    def test_does_not_hammer_database_between_cycles(self):
        worker = self.create_worker(max_cycles=5)
        worker.run()
        self.assertEqual(5, self.mock_select_jobs.call_count)
        self.assertEqual(5, self.mock_sleep.call_count)

    def test_honors_interval(self):
        worker = self.create_worker(interval=timedelta(seconds=1234))
        worker.run()
        self.assertEqual(call(1234), self.mock_sleep.call_args)

    def test_logs_empty_cycles(self):
        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Nothing to do; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_jobs_failing_during_execution(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_ERROR)
        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Error)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_jobs_failing_during_geometry_resolution(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(created_on=LAST_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.side_effect = piazza.ServerError(404)

        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Success)',
            'INFO - <001/test-job-id> Resolving detections data ID (via <test-execution-output-id>)',
            'ERROR - <001/test-job-id> Could not resolve detections data ID: during postprocessing, could not fetch execution output: Piazza server error (HTTP 404)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_jobs_failing_during_geometry_retrieval(self):
        def getfile(_, id_):
            if id_ == 'test-execution-output-id':
                return Mock(json=lambda: create_execution_output())
            raise piazza.ServerError(404)

        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(created_on=LAST_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.side_effect = getfile

        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Success)',
            'INFO - <001/test-job-id> Resolving detections data ID (via <test-execution-output-id>)',
            'INFO - <001/test-job-id> Fetching detections from Piazza',
            'ERROR - <001/test-job-id> Could not fetch data ID <test-detections-id>: Piazza server error (HTTP 404)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_jobs_failing_during_geometry_insertion(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(created_on=LAST_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.return_value.json.return_value = create_execution_output()
        self.mock_getfile.return_value.text = 'lorem ipsum'
        self.mock_insert_detections.side_effect = helpers.create_database_error()

        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Success)',
            'INFO - <001/test-job-id> Resolving detections data ID (via <test-execution-output-id>)',
            'INFO - <001/test-job-id> Fetching detections from Piazza',
            'INFO - <001/test-job-id> Saving detections to database (0.0MB)',
            'ERROR - <001/test-job-id> Could not save status and detections to database',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_jobs_that_are_still_running(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_RUNNING)
        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Running)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_jobs_that_succeed(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.return_value.json.return_value = create_execution_output()
        self.mock_getfile.return_value.text = 'X' * 2048000
        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Success)',
            'INFO - <001/test-job-id> Resolving detections data ID (via <test-execution-output-id>)',
            'INFO - <001/test-job-id> Fetching detections from Piazza',
            'INFO - <001/test-job-id> Saving detections to database (2.0MB)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_jobs_that_time_out(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(created_on=LAST_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_RUNNING)
        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Running)',
            'WARNING - <001/test-job-id> appears to have stalled and will no longer be tracked',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_piazza_server_errors(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(created_on=LAST_WEEK)]
        self.mock_getstatus.side_effect = piazza.ServerError(500)
        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'ERROR - <001/test-job-id> call to Piazza failed: Piazza server error (HTTP 500)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_piazza_response_parsing_errors(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(created_on=LAST_WEEK)]
        self.mock_getstatus.side_effect = piazza.InvalidResponse('test-error', 'lorem ipsum')
        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'ERROR - <001/test-job-id> call to Piazza failed: invalid Piazza response: test-error',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_logs_piazza_auth_failures(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(created_on=LAST_WEEK)]
        self.mock_getstatus.side_effect = piazza.Unauthorized()
        logstream = self.create_logstream()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'ERROR - <001/test-job-id> credentials rejected during polling!',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], logstream.getvalue().splitlines())

    def test_throws_when_database_throws_during_discovery(self):
        self.mock_select_jobs.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            worker = self.create_worker()
            worker.run()

    def test_throws_when_database_throws_during_update(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_CANCELLED)
        self.mock_update_status.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            worker = self.create_worker()
            worker.run()

    def test_updates_status_for_job_failing_during_execution(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_ERROR)
        worker = self.create_worker()
        worker.run()
        self.assertEqual([call(self._mockdb, job_id='test-job-id', status='Error')],
                         self.mock_update_status.call_args_list)
        self.assertEqual([call(self._mockdb, job_id='test-job-id', execution_step=jobs.STEP_ALGORITHM,
                               error_message='Job failed during algorithm execution')],
                         self.mock_insert_job_failure.call_args_list)

    def test_updates_status_for_job_timing_out_while_queued(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(created_on=LAST_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUBMITTED)
        worker = self.create_worker()
        worker.run()
        self.assertEqual([call(self._mockdb, job_id='test-job-id', status='Timed Out')],
                         self.mock_update_status.call_args_list)
        self.assertEqual([call(self._mockdb, job_id='test-job-id', execution_step=jobs.STEP_QUEUED,
                               error_message='Submission wait time exceeded')],
                         self.mock_insert_job_failure.call_args_list)

    def test_updates_status_for_job_timing_out_while_processing(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(created_on=LAST_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_RUNNING)
        worker = self.create_worker()
        worker.run()
        self.assertEqual([call(self._mockdb, job_id='test-job-id', status='Timed Out')],
                         self.mock_update_status.call_args_list)
        self.assertEqual([call(self._mockdb, job_id='test-job-id', execution_step=jobs.STEP_PROCESSING,
                               error_message='Processing time exceeded')],
                         self.mock_insert_job_failure.call_args_list)

    def test_updates_status_for_job_failing_during_geometry_resolution(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.side_effect = piazza.ServerError(500)

        worker = self.create_worker()
        worker.run()
        self.assertEqual([call(self._mockdb, job_id='test-job-id', status='Error')],
                         self.mock_update_status.call_args_list)
        self.assertEqual([call(self._mockdb, job_id='test-job-id', execution_step=jobs.STEP_RESOLVE,
                               error_message='during postprocessing, could not fetch execution output: Piazza server error (HTTP 500)')],
                         self.mock_insert_job_failure.call_args_list)

    def test_updates_status_for_job_failing_during_geometry_retrieval(self):
        def getfile(_, id_):
            if id_ == 'test-execution-output-id':
                return Mock(json=lambda: create_execution_output())
            raise piazza.ServerError(404)

        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.side_effect = getfile

        worker = self.create_worker()
        worker.run()
        self.assertEqual([call(self._mockdb, job_id='test-job-id', status='Error')],
                         self.mock_update_status.call_args_list)
        self.assertEqual([call(self._mockdb, job_id='test-job-id', execution_step=jobs.STEP_COLLECT_GEOJSON,
                               error_message='Could not retrieve GeoJSON from Piazza')],
                         self.mock_insert_job_failure.call_args_list)

    def test_updates_status_for_job_failing_during_geometry_insertion(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.return_value.json.return_value = create_execution_output()
        self.mock_getfile.return_value.text = 'lorem ipsum'
        self.mock_insert_detections.side_effect = helpers.create_database_error()

        worker = self.create_worker()
        worker.run()
        self.assertEqual([call(self._mockdb, job_id='test-job-id', status='Error')],
                         self.mock_update_status.call_args_list)
        self.assertEqual([call(self._mockdb, job_id='test-job-id', execution_step=jobs.STEP_COLLECT_GEOJSON,
                               error_message='Could not insert GeoJSON to database')],
                         self.mock_insert_job_failure.call_args_list)

    def test_updates_status_for_successful_job(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.return_value.json.return_value = create_execution_output()
        self.mock_getfile.return_value.text = 'test-feature-collection'

        worker = self.create_worker()
        worker.run()
        self.assertEqual([call(self._mockdb, job_id='test-job-id', feature_collection='test-feature-collection')],
                         self.mock_insert_detections.call_args_list)
        self.assertEqual([call(self._mockdb, job_id='test-job-id', status='Success')],
                         self.mock_update_status.call_args_list)

    def test_can_handle_multi_record_cycles(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [
            create_job_db_summary('test-job-1'),
            create_job_db_summary('test-job-2'),
            create_job_db_summary('test-job-3'),
            create_job_db_summary('test-job-4'),
        ]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.return_value.json.return_value = create_execution_output()
        self.mock_getfile.return_value.text = 'test-feature-collection'

        worker = self.create_worker()
        worker.run()
        self.assertEqual(1, self.mock_select_jobs.call_count)
        self.assertEqual(4, self.mock_getstatus.call_count)
        self.assertEqual(8, self.mock_getfile.call_count)
        self.assertEqual(4, self.mock_insert_detections.call_count)
        self.assertEqual(4, self.mock_update_status.call_count)

    def test_can_handle_large_number_of_cycles(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_RUNNING)
        worker = self.create_worker(max_cycles=1000, interval=timedelta(0))
        worker.run()
        self.assertEqual(1000, self.mock_select_jobs.call_count)
        self.assertEqual(1000, self.mock_getstatus.call_count)


#
# Helpers
#

def create_algorithm():
    return bfapi.service.algorithms.Algorithm(
        bands=('test-algo-band-1', 'test-algo-band-2'),
        description='test-algo-description',
        interface='test-algo-interface',
        max_cloud_cover=42,
        name='test-algo-name',
        service_id='test-algo-id',
        url='test-algo-url',
        version='test-algo-version',
    )


def create_execution_output():
    return {
        'OutFiles': {
            'shoreline.geojson': 'test-detections-id',
        },
    }


def create_job_db_record(job_id: str = 'test-job-id'):
    return {
        'algorithm_name': 'test-algo-name',
        'algorithm_version': 'test-algo-version',
        'created_by': 'test-creator',
        'created_on': datetime.utcnow(),
        'detections_id': 'test-detections-id',
        'geometry': '{"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]}',
        'job_id': job_id,
        'name': 'test-name',
        'scene_capture_date': datetime.utcnow(),
        'scene_sensor_name': 'test-scene-sensor-name',
        'scene_id': 'test-scene-id',
        'status': 'test-status',
        'tide': 5.4321,
        'tide_min_24h': -10.0,
        'tide_max_24h': 10.0,
    }


def create_job_db_summary(job_id: str = 'test-job-id', created_on: datetime = None):
    return {
        'job_id': job_id,
        'created_on': created_on if created_on else datetime.utcnow(),
    }


def create_scene():
    return bfapi.service.scenes.Scene(
        bands={
            'test-algo-band-1': 'lorem',
            'test-algo-band-2': 'ipsum',
        },
        capture_date=datetime.utcfromtimestamp(1400000000),
        cloud_cover=33,
        geometry={"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
        resolution=15,
        scene_id='test-scene-id',
        sensor_name='test-sensor-name',
        uri='test-uri',
    )


#
# Fixtures
#

RESPONSE_TIDE = """{
  "locations": [
    {
      "dtg": "2016-01-01-01-01",
      "lat": 30,
      "lon": 30,
      "results": {
        "currentTide": 2.6171416113995245,
        "maximumTide24Hours": 2.6171416113995245,
        "minimumTide24Hours": 2.512895346997775
      }
    }
  ]
}"""

RESPONSE_TIDE_NIL = r"""{
  "locations": [
    {
      "dtg": "2016-01-01-01-01",
      "lat": 300,
      "lon": 300,
      "results": "{\"minimumTide24Hours\": \"null\", \"currentTide\": \"null\", \"maximumTide24Hours\": \"null\"}"
    }
  ]
}"""
