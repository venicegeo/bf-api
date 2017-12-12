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
from datetime import datetime, timedelta
from unittest.mock import call, patch, Mock

import requests_mock as rm

from test import helpers

from bfapi.db import DatabaseError
from bfapi.service import algorithms, jobs, piazza, scenes

ONE_WEEK = timedelta(days=7.0, hours=12, minutes=34, seconds=56)
LAST_WEEK = datetime.utcnow() - ONE_WEEK


class CreateJobTest(unittest.TestCase):
    maxDiff = 4096

    def setUp(self):
        self._mockdb = helpers.mock_database()
        self.logger = helpers.get_logger('bfapi.service.jobs')

        self.mock_requests = rm.Mocker()  # type: rm.Mocker
        self.mock_requests.start()
        self.addCleanup(self.mock_requests.stop)
        self.mock_execute = self.create_mock('bfapi.service.piazza.execute')
        self.mock_activate_scene = self.create_mock('bfapi.service.scenes.activate')
        self.mock_get_scene = self.create_mock('bfapi.service.scenes.get')
        self.mock_get_algo = self.create_mock('bfapi.service.algorithms.get')
        self.mock_insert_job = self.create_mock('bfapi.db.jobs.insert_job')
        self.mock_insert_job_user = self.create_mock('bfapi.db.jobs.insert_job_user')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_returns_job(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)

    def test_assigns_correct_algorithm_name(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-algo-name', job.algorithm_name)

    def test_assigns_correct_algorithm_version(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-algo-version', job.algorithm_version)

    def test_assigns_correct_created_by(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-user-id', job.created_by)

    def test_assigns_correct_created_on(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual(datetime.utcnow().date(), job.created_on.date())

    def test_assigns_correct_geometry(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual({"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
                         job.geometry)

    def test_assigns_correct_job_id(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_execute.return_value = 'test-new-job-id'
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-new-job-id', job.job_id)

    def test_assigns_correct_name(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-name', job.name)

    def test_assigns_correct_time_of_collect(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('2014-05-13T16:53:20', job.scene_time_of_collect.isoformat())

    def test_assigns_correct_scene_sensor_name(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-sensor-name', job.scene_sensor_name)

    def test_assigns_correct_scene_id(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('test-scene-id', job.scene_id)

    def test_assigns_correct_status(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual('Pending', job.status)

    def test_assigns_correct_tide(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual(0.5, job.tide)

    def test_assigns_correct_tide_min(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual(0.0, job.tide_min_24h)

    def test_assigns_correct_tide_max(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        job = jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertIsInstance(job, jobs.Job)
        self.assertEqual(1.0, job.tide_max_24h)

    def test_creates_database_record(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual(1, self.mock_insert_job.call_count)

    def test_saves_correct_algorithm_name_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('test-algo-name', self.mock_insert_job.call_args[1]['algorithm_name'])

    def test_saves_correct_algorithm_version_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('test-algo-version', self.mock_insert_job.call_args[1]['algorithm_version'])

    def test_saves_correct_user_id_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('test-user-id', self.mock_insert_job.call_args[1]['user_id'])

    def test_saves_correct_job_id_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_execute.return_value = 'test-new-job-id'
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('test-new-job-id', self.mock_insert_job.call_args[1]['job_id'])

    def test_saves_correct_name_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('test-name', self.mock_insert_job.call_args[1]['name'])

    def test_saves_correct_scene_id_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('test-scene-id', self.mock_insert_job.call_args[1]['scene_id'])

    def test_saves_correct_status_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('Pending', self.mock_insert_job.call_args[1]['status'])

    def test_saves_correct_tide_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual(0.5, self.mock_insert_job.call_args[1]['tide'])

    def test_saves_correct_tide_min_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual(0.0, self.mock_insert_job.call_args[1]['tide_min_24h'])

    def test_saves_correct_tide_max_to_database(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual(1.0, self.mock_insert_job.call_args[1]['tide_max_24h'])

    def test_fetches_correct_scene(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual(call('test-scene-id', 'test-planet-api-key'), self.mock_get_scene.call_args)

    def test_preemptively_activates_scene(self):
        self.mock_get_algo.return_value = create_algorithm()
        scene = create_scene()
        self.mock_get_scene.return_value = scene
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual(call(scene, 'test-planet-api-key', 'test-user-id'), self.mock_activate_scene.call_args)

    def test_sends_correct_payload_to_piazza_pzsvc_ossim(self):
        self.mock_get_algo.return_value = create_algorithm('pzsvc-ossim')
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('test-algo-id', self.mock_execute.call_args[0][0])
        self.assertEqual({
            'cmd': 'shoreline' +
                   ' --image multispectral.TIF' +
                   ' --projection geo-scaled' +
                   ' --threshold 0.5' +
                   ' --tolerance 0.075' +
                   ' shoreline.geojson',
            'inExtFiles': ['https://bf-api.test.localdomain/v0/scene/test-scene-id?planet_api_key=test-planet-api-key'],
            'inExtNames': ['multispectral.TIF'],
            'outGeoJson': ['shoreline.geojson'],
            'userID': 'test-user-id',
        }, json.loads(self.mock_execute.call_args[0][1]['body']['content']))

    def test_sends_correct_payload_to_piazza_pzsvc_ndwi_py_for_planetscope(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene(platform=scenes.PLATFORM_PLANETSCOPE)
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('test-algo-id', self.mock_execute.call_args[0][0])
        self.assertEqual({
            'cmd': '-i multispectral.TIF --bands 2 4 --basename shoreline --smooth 1.0 --coastmask True',
            'inExtFiles': ['https://bf-api.test.localdomain/v0/scene/test-scene-id?planet_api_key=test-planet-api-key'],
            'inExtNames': ['multispectral.TIF'],
            'outGeoJson': ['shoreline.geojson'],
            'userID': 'test-user-id',
        }, json.loads(self.mock_execute.call_args[0][1]['body']['content']))

    def test_sends_correct_payload_to_piazza_pzsvc_ndwi_py_for_rapideye(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene(platform=scenes.PLATFORM_RAPIDEYE)
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual('test-algo-id', self.mock_execute.call_args[0][0])
        self.assertEqual({
            'cmd': '-i multispectral.TIF --bands 2 5 --basename shoreline --smooth 1.0 --coastmask True',
            'inExtFiles': ['https://bf-api.test.localdomain/v0/scene/test-scene-id?planet_api_key=test-planet-api-key'],
            'inExtNames': ['multispectral.TIF'],
            'outGeoJson': ['shoreline.geojson'],
            'userID': 'test-user-id',
        }, json.loads(self.mock_execute.call_args[0][1]['body']['content']))

    def test_does_not_create_database_record_if_cannot_start(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_execute.side_effect = piazza.ServerError(500)
        try:
            jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        except:
            pass
        self.assertEqual(0, self.mock_insert_job.call_count)
        self.assertEqual(0, self.mock_insert_job_user.call_count)

    def test_logs_creation_success(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        jobs.create('test-user-id', 'test-scene-id', 'test-service-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual([
            'INFO - Job service initiate create job "test-name" for user "test-user-id" for scene "test-scene-id"',
            'INFO - Dispatching <scene:test-scene-id> to <algo:test-algo-name>',
        ], self.logger.lines)

    def test_logs_creation_failure_during_algorithm_retrieval(self):
        self.mock_get_algo.side_effect = algorithms.NotFound('test-algo-id')
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual([
            'INFO - Job service initiate create job "test-name" for user "test-user-id" for scene "test-scene-id"',
            'ERROR - Preprocessing error: algorithm `test-algo-id` does not exist',
        ], self.logger.lines)

    def test_logs_creation_failure_during_scene_retrieval(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.side_effect = scenes.NotFound('test-scene-id')
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual([
            'INFO - Job service initiate create job "test-name" for user "test-user-id" for scene "test-scene-id"',
            'ERROR - Preprocessing error: scene `test-scene-id` not found in catalog',
        ], self.logger.lines)

    def test_logs_creation_failure_during_execution(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_execute.side_effect = piazza.ServerError(400)
        with self.assertRaises(piazza.ServerError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual([
            'INFO - Job service initiate create job "test-name" for user "test-user-id" for scene "test-scene-id"',
            'INFO - Dispatching <scene:test-scene-id> to <algo:test-algo-name>',
            'ERROR - Could not execute via Piazza: Piazza server error (HTTP 400)'
        ], self.logger.lines)

    def test_logs_creation_failure_during_database_insert(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_insert_job.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)
        self.assertEqual([
            'INFO - Job service initiate create job "test-name" for user "test-user-id" for scene "test-scene-id"',
            'INFO - Dispatching <scene:test-scene-id> to <algo:test-algo-name>',
            "ERROR - Could not save job to database",
        ], self.logger.lines)

    def test_throws_when_piazza_throws(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_execute.side_effect = piazza.ServerError(500)
        with self.assertRaises(piazza.ServerError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)

    def test_throws_when_database_insertion_fails(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.return_value = create_scene()
        self.mock_insert_job.side_effect = helpers.create_database_error()
        with self.assertRaises(DatabaseError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)

    def test_throws_when_algorithm_not_found(self):
        self.mock_get_algo.side_effect = algorithms.NotFound('test-algo-id')
        self.mock_get_scene.return_value = create_scene()
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)

    def test_throws_when_scene_not_found(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.side_effect = scenes.NotFound('test-scene-id')
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)

    def test_throws_when_catalog_is_unreachable(self):
        self.mock_get_algo.return_value = create_algorithm()
        self.mock_get_scene.side_effect = scenes.CatalogError()
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)

    def test_throws_when_algorithm_is_unknown(self):
        self.mock_get_algo.return_value = create_algorithm('unknown-algorithm')
        self.mock_get_scene.return_value = create_scene()
        with self.assertRaises(jobs.PreprocessingError):
            jobs.create('test-user-id', 'test-scene-id', 'test-algo-id', 'test-name', 'test-planet-api-key', True)


@patch('bfapi.db.jobs.delete_job_user')
@patch('bfapi.db.jobs.exists')
class ForgetJobTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self.logger = helpers.get_logger('bfapi.service.jobs')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

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
        self.logger = helpers.get_logger('bfapi.service.jobs')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

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

    def test_assigns_correct_time_of_collect(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_all('test-user-id').pop()
        self.assertEqual(datetime.utcnow().date(), job.scene_time_of_collect.date())

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
        self.logger = helpers.get_logger('bfapi.service.jobs')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

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
        self.logger = helpers.get_logger('bfapi.service.jobs')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

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

    def test_assigns_correct_time_of_collect(self, mock_select: Mock, _):
        mock_select.return_value.fetchone.return_value = create_job_db_record()
        job = jobs.get('test-user-id', 'test-job-id')
        self.assertEqual(datetime.utcnow().date(), job.scene_time_of_collect.date())

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
        self.logger = helpers.get_logger('bfapi.service.jobs')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

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

    def test_assigns_correct_time_of_collect(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_productline('test-productline-id', LAST_WEEK).pop()
        self.assertEqual(datetime.utcnow().date(), job.scene_time_of_collect.date())

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
        self.logger = helpers.get_logger('bfapi.service.jobs')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

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

    def test_assigns_correct_time_of_collect(self, mock: Mock):
        mock.return_value.fetchall.return_value = [create_job_db_record()]
        job = jobs.get_by_scene('test-scene-id').pop()
        self.assertEqual(datetime.utcnow().date(), job.scene_time_of_collect.date())

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
        self.logger = helpers.get_logger('bfapi.service.jobs')

    def tearDown(self):
        jobs.stop_worker()
        self._mockdb.destroy()
        self.logger.destroy()

    def test_module_does_not_start_worker_until_invoked(self, _):
        self.assertIsNone(jobs._worker)

    def test_starts_worker(self, _):
        jobs.start_worker()
        stub = jobs._worker.start  # type: Mock
        self.assertEqual(1, stub.call_count)

    def test_retains_worker_instance(self, _):
        jobs.start_worker()
        self.assertIsNotNone(jobs._worker)

    def test_passes_correct_params_to_worker(self, mock: Mock):
        jobs.start_worker(
            job_ttl=timedelta(12),
            interval=timedelta(34),
        )
        self.assertEqual((timedelta(12), timedelta(34)), mock.call_args[0])

    def test_throws_if_worker_already_exists(self, _):
        jobs.start_worker()
        with self.assertRaisesRegex(jobs.Error, 'worker already started'):
            jobs.start_worker()


@patch('bfapi.service.jobs.Worker')
class StopWorkerTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self.logger = helpers.get_logger('bfapi.service.jobs')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()

    def test_stops_worker(self, _):
        jobs.start_worker()
        stub = jobs._worker.terminate  # type: Mock
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
        self.logger = helpers.get_logger('bfapi.service.jobs.worker')
        self._logger_for_module = helpers.get_logger('bfapi.service.jobs')
        self._logger_for_module.disabled = True

        self.mock_sleep = self.create_mock('time.sleep')
        self.mock_thread = self.create_mock('threading.Thread')
        self.mock_getfile = self.create_mock('bfapi.service.piazza.get_file')
        self.mock_getstatus = self.create_mock('bfapi.service.piazza.get_status')
        self.mock_insert_detections = self.create_mock('bfapi.db.jobs.insert_detection')
        self.mock_select_jobs = self.create_mock('bfapi.db.jobs.select_outstanding_jobs')
        self.mock_select_jobs.return_value.fetchall.return_value = []
        self.mock_update_status = self.create_mock('bfapi.db.jobs.update_status')
        self.mock_insert_job_failure = self.create_mock('bfapi.db.jobs.insert_job_failure')

    def tearDown(self):
        self._mockdb.destroy()
        self.logger.destroy()
        self._logger_for_module.disabled = False

    def create_mock(self, target_name):
        patcher = patch(target_name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def create_worker(self, *, max_cycles=1, interval=timedelta(1)):
        worker = jobs.Worker(job_ttl=timedelta(1), interval=interval)
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
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Nothing to do; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_jobs_failing_during_execution(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_ERROR)
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Error; age=7 days, 12:34:56)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_jobs_failing_during_geometry_resolution(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=ONE_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.side_effect = piazza.ServerError(404)

        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Success; age=7 days, 12:34:56)',
            'INFO - <001/test-job-id> Resolving detections data ID (via <test-execution-output-id>)',
            'ERROR - <001/test-job-id> Could not resolve detections data ID: during postprocessing, could not fetch execution output: Piazza server error (HTTP 404)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_jobs_failing_during_geometry_retrieval(self):
        def getfile(id_):
            if id_ == 'test-execution-output-id':
                return Mock(json=lambda: create_execution_output())
            raise piazza.ServerError(404)

        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=ONE_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.side_effect = getfile

        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Success; age=7 days, 12:34:56)',
            'INFO - <001/test-job-id> Resolving detections data ID (via <test-execution-output-id>)',
            'INFO - <001/test-job-id> Fetching detections from Piazza',
            'ERROR - <001/test-job-id> Could not fetch data ID <test-detections-id>: Piazza server error (HTTP 404)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_jobs_failing_during_geometry_insertion(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=ONE_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.return_value.json.return_value = create_execution_output()
        self.mock_getfile.return_value.text = 'lorem ipsum'
        self.mock_insert_detections.side_effect = helpers.create_database_error()

        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Success; age=7 days, 12:34:56)',
            'INFO - <001/test-job-id> Resolving detections data ID (via <test-execution-output-id>)',
            'INFO - <001/test-job-id> Fetching detections from Piazza',
            'INFO - <001/test-job-id> Saving detections to database (0.0MB)',
            'ERROR - <001/test-job-id> Could not save status and detections to database',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_jobs_that_are_still_running(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=timedelta(minutes=20))]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_RUNNING)
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Running; age=0:20:00)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_jobs_that_succeed(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUCCESS, data_id='test-execution-output-id')
        self.mock_getfile.return_value.json.return_value = create_execution_output()
        self.mock_getfile.return_value.text = 'X' * 2048000
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Success; age=7 days, 12:34:56)',
            'INFO - <001/test-job-id> Resolving detections data ID (via <test-execution-output-id>)',
            'INFO - <001/test-job-id> Fetching detections from Piazza',
            'INFO - <001/test-job-id> Saving detections to database (2.0MB)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_jobs_that_time_out(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=ONE_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_RUNNING)
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Running; age=7 days, 12:34:56)',
            'WARNING - <001/test-job-id> appears to have stalled and will no longer be tracked',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_piazza_server_errors(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=ONE_WEEK)]
        self.mock_getstatus.side_effect = piazza.ServerError(500)
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'ERROR - <001/test-job-id> call to Piazza failed: Piazza server error (HTTP 500)',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_piazza_response_parsing_errors(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=ONE_WEEK)]
        self.mock_getstatus.side_effect = piazza.InvalidResponse('test-error', 'lorem ipsum')
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'ERROR - <001/test-job-id> call to Piazza failed: invalid Piazza response: test-error',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_logs_piazza_auth_failures(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=ONE_WEEK)]
        self.mock_getstatus.side_effect = piazza.Unauthorized()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'ERROR - <001/test-job-id> credentials rejected during polling!',
            'INFO - Cycle complete; next run at {:%TZ}'.format(datetime.utcnow()),
            'INFO - Stopped',
        ], self.logger.lines)

    def test_report_error_and_retry_when_database_throws_during_discovery(self):
        self.mock_select_jobs.side_effect = helpers.create_database_error()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'ERROR - Could not list running jobs',
            "WARNING - Recovered from failure (attempt 1 of 3); DatabaseError: (builtins.Exception) test-error [SQL: 'test-query']",
            'INFO - Stopped',
        ], self.logger.lines)

    def test_report_error_and_retry_when_database_throws_during_update(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary()]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_CANCELLED)
        self.mock_update_status.side_effect = helpers.create_database_error()
        worker = self.create_worker()
        worker.run()
        self.assertEqual([
            'INFO - Begin cycle for 1 records',
            'INFO - <001/test-job-id> polled (Cancelled; age=7 days, 12:34:56)',
            "WARNING - Recovered from failure (attempt 1 of 3); DatabaseError: (builtins.Exception) test-error [SQL: 'test-query']",
            'INFO - Stopped',
        ], self.logger.lines)

    def test_worker_retry_then_permanent_fail(self):
        self.mock_select_jobs.side_effect = helpers.create_database_error()
        worker = self.create_worker(max_cycles=4)
        worker.run()
        self.assertEqual([
            'ERROR - Could not list running jobs',
            "WARNING - Recovered from failure (attempt 1 of 3); DatabaseError: (builtins.Exception) test-error [SQL: 'test-query']",
            'ERROR - Could not list running jobs',
            "WARNING - Recovered from failure (attempt 2 of 3); DatabaseError: (builtins.Exception) test-error [SQL: 'test-query']",
            'ERROR - Could not list running jobs',
            "WARNING - Recovered from failure (attempt 3 of 3); DatabaseError: (builtins.Exception) test-error [SQL: 'test-query']",
            'ERROR - Could not list running jobs',
            "ERROR - Worker failed more than 3 times and will not be recovered",

            # Start stack trace truncation
            'Traceback (most recent call last):',
        ], self.logger.lines[0:9])
        self.assertEqual([
            "sqlalchemy.exc.DatabaseError: (builtins.Exception) test-error [SQL: 'test-query']",
            # End stack trace truncation

            'INFO - Stopped',
        ], self.logger.lines[-2:])

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
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=ONE_WEEK)]
        self.mock_getstatus.return_value = piazza.Status(piazza.STATUS_SUBMITTED)
        worker = self.create_worker()
        worker.run()
        self.assertEqual([call(self._mockdb, job_id='test-job-id', status='Timed Out')],
                         self.mock_update_status.call_args_list)
        self.assertEqual([call(self._mockdb, job_id='test-job-id', execution_step=jobs.STEP_QUEUED,
                               error_message='Submission wait time exceeded')],
                         self.mock_insert_job_failure.call_args_list)

    def test_updates_status_for_job_timing_out_while_processing(self):
        self.mock_select_jobs.return_value.fetchall.return_value = [create_job_db_summary(age=ONE_WEEK)]
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
        def getfile(id_):
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

def create_algorithm(algo_interface='pzsvc-ndwi-py'):
    return algorithms.Algorithm(
        description='test-algo-description',
        interface=algo_interface,
        max_cloud_cover=42,
        name='test-algo-name',
        service_id='test-algo-id',
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
        'captured_on': datetime.utcnow(),
        'sensor_name': 'test-scene-sensor-name',
        'scene_id': 'test-scene-id',
        'status': 'test-status',
        'tide': 5.4321,
        'tide_min_24h': -10.0,
        'tide_max_24h': 10.0,
        'compute_mask': True
    }


def create_job_db_summary(job_id: str = 'test-job-id', age: timedelta = None):
    return {
        'job_id': job_id,
        'age': age or ONE_WEEK,
    }


def create_scene(platform: str = scenes.PLATFORM_PLANETSCOPE):
    return scenes.Scene(
        capture_date=datetime.utcfromtimestamp(1400000000),
        cloud_cover=33,
        geometry={"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
        platform=platform,
        resolution=15,
        scene_id='test-scene-id',
        sensor_name='test-sensor-name',
        status=scenes.STATUS_ACTIVE,
        tide=0.5,
        tide_min=0.0,
        tide_max=1.0,
        uri='test-uri',
    )
