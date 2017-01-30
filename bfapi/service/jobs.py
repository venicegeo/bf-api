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
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List

from bfapi import db
from bfapi.config import JOB_TTL, JOB_WORKER_INTERVAL
from bfapi.service import algorithms, scenes, piazza

FORMAT_DTG = '%Y-%m-%d-%H-%M'
FORMAT_TIME = '%TZ'
STATUS_TIMED_OUT = 'Timed Out'
STEP_ALGORITHM = 'runtime:algorithm'
STEP_COLLECT_GEOJSON = 'postprocessing:collect_geojson'
STEP_POLLING = 'runtime:polling-for-status'
STEP_PROCESSING = 'runtime:processing'
STEP_QUEUED = 'runtime:queued'
STEP_RESOLVE = 'postprocessing:resolving_detections_data_id'

_worker = None  # type: Worker

#
# Types
#

class Job:
    def __init__(
            self,
            *,
            algorithm_name: str,
            algorithm_version: str,
            created_by: str,
            created_on: datetime,
            geometry: dict,
            job_id: str,
            name: str,
            scene_sensor_name: str,
            scene_time_of_collect: datetime,
            scene_id: str,
            status: str,
            tide: float,
            tide_min_24h: float,
            tide_max_24h: float):
        self.algorithm_name = algorithm_name
        self.algorithm_version = algorithm_version
        self.created_by = created_by
        self.created_on = created_on
        self.geometry = geometry
        self.job_id = job_id
        self.name = name
        self.scene_time_of_collect = scene_time_of_collect
        self.scene_sensor_name = scene_sensor_name
        self.scene_id = scene_id
        self.status = status
        self.tide = tide
        self.tide_min_24h = tide_min_24h
        self.tide_max_24h = tide_max_24h

    def serialize(self):
        return {
            'type': 'Feature',
            'id': self.job_id,
            'geometry': self.geometry,
            'properties': {
                'algorithm_name': self.algorithm_name,
                'algorithm_version': self.algorithm_version,
                'created_by': self.created_by,
                'created_on': _serialize_dt(self.created_on),
                'name': self.name,
                'scene_time_of_collect': _serialize_dt(self.scene_time_of_collect),
                'scene_id': self.scene_id,
                'scene_sensor_name': self.scene_sensor_name,
                'status': self.status,
                'tide': self.tide,
                'tide_min_24h': self.tide_min_24h,
                'tide_max_24h': self.tide_max_24h,
                'type': 'JOB',
            }
        }


#
# Actions
#

def create(
        user_id: str,
        scene_id: str,
        service_id: str,
        job_name: str,
        planet_api_key: str) -> Job:
    log = logging.getLogger(__name__)

    # Fetch prerequisites
    try:
        algorithm = algorithms.get(service_id)
        scene = scenes.get(scene_id, planet_api_key)
        scenes.activate(scene, planet_api_key)
    except (algorithms.NotFound,
            algorithms.ValidationError,
            scenes.MalformedSceneID,
            scenes.CatalogError,
            scenes.NotFound,
            scenes.ValidationError) as err:
        log.error('Preprocessing error: %s', err)
        raise PreprocessingError(err)

    # Determine GeoTIFF URLs
    geotiff_filenames = ['multispectral.TIF']
    geotiff_urls = [scenes.create_download_url(scene.id, planet_api_key)]

    # Dispatch to Piazza
    try:
        log.info('Dispatching <scene:%s> to <algo:%s>', scene_id, algorithm.name)
        cli_cmd = _create_algorithm_cli_cmd(algorithm.interface, geotiff_filenames, scene.platform)
        job_id = piazza.execute(algorithm.service_id, {
            'body': {
                'content': json.dumps({
                    'cmd': cli_cmd,
                    'inExtFiles': geotiff_urls,
                    'inExtNames': geotiff_filenames,
                    'outGeoJson': ['shoreline.geojson'],
                    'userID': user_id,
                }),
                'type': 'body',
                'mimeType': 'application/json',
            },
        })
    except piazza.Error as err:
        log.error('Could not execute via Piazza: %s', err)
        raise

    # Record the data
    log.debug('Saving job record <%s>', job_id)
    conn = db.get_connection()
    transaction = conn.begin()
    try:
        db.jobs.insert_job(
            conn,
            algorithm_id=algorithm.service_id,
            algorithm_name=algorithm.name,
            algorithm_version=algorithm.version,
            job_id=job_id,
            name=job_name,
            scene_id=scene_id,
            status=piazza.STATUS_PENDING,
            user_id=user_id,
            tide=scene.tide,
            tide_min_24h=scene.tide_min,
            tide_max_24h=scene.tide_max,
        )
        db.jobs.insert_job_user(
            conn,
            job_id=job_id,
            user_id=user_id,
        )
        transaction.commit()
    except db.DatabaseError as err:
        transaction.rollback()
        log.error('Could not save job to database')
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

    return Job(
        algorithm_name=algorithm.name,
        algorithm_version=algorithm.version,
        created_by=user_id,
        created_on=datetime.utcnow(),
        geometry=scene.geometry,
        job_id=job_id,
        name=job_name,
        scene_time_of_collect=scene.capture_date,
        scene_sensor_name=scene.sensor_name,
        scene_id=scene_id,
        status=piazza.STATUS_PENDING,
        tide=scene.tide,
        tide_min_24h=scene.tide_min,
        tide_max_24h=scene.tide_max,
    )

def forget(user_id: str, job_id: str) -> None:
    log = logging.getLogger(__name__)
    conn = db.get_connection()
    try:
        if not db.jobs.exists(conn, job_id=job_id):
            raise NotFound(job_id)
        db.jobs.delete_job_user(conn, job_id=job_id, user_id=user_id)
    except db.DatabaseError as err:
        log.error('Could not forget <job:%s> for user "%s"', job_id, user_id)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()


def get(user_id: str, job_id: str) -> Job:
    log = logging.getLogger(__name__)
    conn = db.get_connection()

    try:
        row = db.jobs.select_job(conn, job_id=job_id).fetchone()
        if not row:
            raise NotFound(job_id)

        # Add job to user's tracked jobs list
        db.jobs.insert_job_user(conn, job_id=job_id, user_id=user_id)
    except db.DatabaseError as err:
        log.error('Could not get <job:%s> for user "%s"', job_id, user_id)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

    return Job(
        algorithm_name=row['algorithm_name'],
        algorithm_version=row['algorithm_version'],
        created_by=row['created_by'],
        created_on=row['created_on'],
        geometry=json.loads(row['geometry']),
        job_id=row['job_id'],
        name=row['name'],
        scene_time_of_collect=row['captured_on'],
        scene_sensor_name=row['sensor_name'],
        scene_id=row['scene_id'],
        status=row['status'],
        tide=row['tide'],
        tide_min_24h=row['tide_min_24h'],
        tide_max_24h=row['tide_max_24h'],
    )


def get_all(user_id: str) -> List[Job]:
    log = logging.getLogger(__name__)
    conn = db.get_connection()

    try:
        cursor = db.jobs.select_jobs_for_user(conn, user_id=user_id)
    except db.DatabaseError as err:
        log.error('Could not list jobs for user "%s"', user_id)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

    jobs = []
    for row in cursor.fetchall():
        feature = Job(
            algorithm_name=row['algorithm_name'],
            algorithm_version=row['algorithm_version'],
            created_by=row['created_by'],
            created_on=row['created_on'],
            geometry=json.loads(row['geometry']),
            job_id=row['job_id'],
            name=row['name'],
            scene_time_of_collect=row['captured_on'],
            scene_sensor_name=row['sensor_name'],
            scene_id=row['scene_id'],
            status=row['status'],
            tide=row['tide'],
            tide_min_24h=row['tide_min_24h'],
            tide_max_24h=row['tide_max_24h'],
        )
        jobs.append(feature)

    return jobs


def get_by_productline(productline_id: str, since: datetime) -> List[Job]:
    log = logging.getLogger(__name__)
    conn = db.get_connection()

    try:
        cursor = db.jobs.select_jobs_for_productline(conn, productline_id=productline_id, since=since)
    except db.DatabaseError as err:
        log.error('Could not list jobs for <productline:%s>', productline_id)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

    jobs = []
    for row in cursor.fetchall():
        jobs.append(Job(
            algorithm_name=row['algorithm_name'],
            algorithm_version=row['algorithm_version'],
            created_by=row['created_by'],
            created_on=row['created_on'],
            geometry=json.loads(row['geometry']),
            job_id=row['job_id'],
            name=row['name'],
            scene_time_of_collect=row['captured_on'],
            scene_sensor_name=row['sensor_name'],
            scene_id=row['scene_id'],
            status=row['status'],
            tide=row['tide'],
            tide_min_24h=row['tide_min_24h'],
            tide_max_24h=row['tide_max_24h'],
        ))
    return jobs


def get_by_scene(scene_id: str) -> List[Job]:
    log = logging.getLogger(__name__)
    conn = db.get_connection()

    try:
        cursor = db.jobs.select_jobs_for_scene(conn, scene_id=scene_id)
    except db.DatabaseError as err:
        log.error('Could not list jobs for <scene:%s>', scene_id)
        db.print_diagnostics(err)
        raise err
    finally:
        conn.close()

    jobs = []
    for row in cursor.fetchall():
        jobs.append(Job(
            algorithm_name=row['algorithm_name'],
            algorithm_version=row['algorithm_version'],
            created_by=row['created_by'],
            created_on=row['created_on'],
            geometry=json.loads(row['geometry']),
            job_id=row['job_id'],
            name=row['name'],
            scene_time_of_collect=row['captured_on'],
            scene_sensor_name=row['sensor_name'],
            scene_id=row['scene_id'],
            status=row['status'],
            tide=row['tide'],
            tide_min_24h=row['tide_min_24h'],
            tide_max_24h=row['tide_max_24h'],
        ))
    return jobs


def get_detections(job_id: str) -> str:
    """
    Returns a potentially massive stringified GeoJSON feature collection containing all detections
    for a given job.
    """

    log = logging.getLogger(__name__)
    conn = db.get_connection()

    log.info('Packaging detections for <job:%s>', job_id)
    try:
        if not db.jobs.exists(conn, job_id=job_id):
            raise NotFound(job_id)
        geojson = db.jobs.select_detections(conn, job_id=job_id).scalar()
    except db.DatabaseError as err:
        log.error('Could not package detections for <job:%s>', job_id)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

    log.debug('Packaging complete: %d bytes for <job:%s>', len(geojson), job_id)
    return geojson


def start_worker(
        job_ttl: timedelta = JOB_TTL,
        interval: timedelta = JOB_WORKER_INTERVAL):
    global _worker

    if _worker is not None:
        raise Error('worker already started')

    log = logging.getLogger(__name__)
    log.info('Starting worker thread')
    _worker = Worker(job_ttl, interval)
    _worker.start()


def stop_worker():
    global _worker
    if not _worker:
        return
    log = logging.getLogger(__name__)
    log.info('Stopping worker thread')
    _worker.terminate()
    _worker = None


class Worker(threading.Thread):
    def __init__(self, job_ttl: timedelta, interval: timedelta):
        super().__init__()
        self.daemon = True
        self._log = logging.getLogger(__name__ + '.worker')
        self._job_ttl = job_ttl
        self._interval = interval
        self._terminated = False

    def is_terminated(self):
        return self._terminated

    def terminate(self):
        self._terminated = True

    def run(self):
        while not self.is_terminated():
            conn = db.get_connection()
            try:
                rows = db.jobs.select_outstanding_jobs(conn).fetchall()
            except db.DatabaseError as err:
                self._log.error('Could not list running jobs')
                db.print_diagnostics(err)
                raise
            finally:
                conn.close()

            if not rows:
                self._log.info('Nothing to do; next run at %s', (datetime.utcnow() + self._interval).strftime(FORMAT_TIME))
            else:
                self._log.info('Begin cycle for %d records', len(rows))
                for i, row in enumerate(rows, start=1):
                    self._updater(row['job_id'], row['age'], i)
                self._log.info('Cycle complete; next run at %s', (datetime.utcnow() + self._interval).strftime(FORMAT_TIME))

            time.sleep(self._interval.total_seconds())

        self._log.info('Stopped')

    def _updater(self, job_id: str, age: timedelta, index: int):
        log = self._log
        job_ttl = self._job_ttl

        # Get latest status
        try:
            status = piazza.get_status(job_id)
        except piazza.Unauthorized:
            log.error('<%03d/%s> credentials rejected during polling!', index, job_id)
            return
        except (piazza.ServerError, piazza.Error) as err:
            if isinstance(err, piazza.ServerError) and err.status_code == 404:
                log.warning('<%03d/%s> Job not found', index, job_id)
                _save_execution_error(job_id, STEP_POLLING, 'Job not found')
                return
            else:
                log.error('<%03d/%s> call to Piazza failed: %s', index, job_id, err.message)
                return

        # Emit console feedback
        log.info('<%03d/%s> polled (%s; age=%s)', index, job_id, status.status, age)

        # Determine appropriate action by status
        if status.status in (piazza.STATUS_SUBMITTED, piazza.STATUS_PENDING):
            if age > job_ttl:
                log.warning('<%03d/%s> appears to have stalled and will no longer be tracked', index, job_id)
                _save_execution_error(job_id, STEP_QUEUED, 'Submission wait time exceeded', status=STATUS_TIMED_OUT)
                return

            conn = db.get_connection()
            try:
                db.jobs.update_status(conn, job_id=job_id, status=status.status)
            except db.DatabaseError as err:
                log.error('<%03d/%s> Could not save status to database', index, job_id)
                db.print_diagnostics(err)
                return
            finally:
                conn.close()

        elif status.status == piazza.STATUS_RUNNING:
            if age > job_ttl:
                log.warning('<%03d/%s> appears to have stalled and will no longer be tracked', index, job_id)
                _save_execution_error(job_id, STEP_PROCESSING, 'Processing time exceeded', status=STATUS_TIMED_OUT)
                return

            conn = db.get_connection()
            try:
                db.jobs.update_status(conn, job_id=job_id, status=status.status)
            except db.DatabaseError as err:
                log.error('<%03d/%s> Could not save status to database', index, job_id)
                db.print_diagnostics(err)
                return
            finally:
                conn.close()

        elif status.status == piazza.STATUS_SUCCESS:
            log.info('<%03d/%s> Resolving detections data ID (via <%s>)', index, job_id, status.data_id)
            try:
                detections_data_id = _resolve_detections_data_id(status.data_id)
            except PostprocessingError as err:
                log.error('<%03d/%s> Could not resolve detections data ID: %s', index, job_id, err)
                _save_execution_error(job_id, STEP_RESOLVE, str(err))
                return

            log.info('<%03d/%s> Fetching detections from Piazza', index, job_id)
            try:
                geojson = piazza.get_file(detections_data_id).text
            except piazza.ServerError as err:
                log.error('<%03d/%s> Could not fetch data ID <%s>: %s', index, job_id, detections_data_id, err)
                _save_execution_error(job_id, STEP_COLLECT_GEOJSON, 'Could not retrieve GeoJSON from Piazza')
                return

            log.info('<%03d/%s> Saving detections to database (%0.1fMB)', index, job_id, len(geojson) / 1024000)
            conn = db.get_connection()
            transaction = conn.begin()
            try:
                db.jobs.insert_detection(conn, job_id=job_id, feature_collection=geojson)
                db.jobs.update_status(
                    conn,
                    job_id=job_id,
                    status=piazza.STATUS_SUCCESS,
                )
                transaction.commit()
            except db.DatabaseError as err:
                transaction.rollback()
                transaction.close()
                log.error('<%03d/%s> Could not save status and detections to database', index, job_id)
                db.print_diagnostics(err)
                _save_execution_error(job_id, STEP_COLLECT_GEOJSON, 'Could not insert GeoJSON to database')
                return
            finally:
                conn.close()

        elif status.status in (piazza.STATUS_ERROR, piazza.STATUS_FAIL):
            # FIXME -- use heuristics to generate a more descriptive error message
            _save_execution_error(job_id, STEP_ALGORITHM, 'Job failed during algorithm execution')

        elif status.status == piazza.STATUS_CANCELLED:
            _save_execution_error(job_id, STEP_ALGORITHM, 'Job was cancelled', status=piazza.STATUS_CANCELLED)


#
# Helpers
#

def _create_algorithm_cli_cmd(
        algo_interface: str,
        geotiff_filenames: list,
        scene_platform: str) -> str:
    log = logging.getLogger(__name__)
    if algo_interface == 'pzsvc-ossim':
        return ' '.join([
            'shoreline',
            '--image ' + ','.join(geotiff_filenames),
            '--projection geo-scaled',
            '--threshold 0.5',
            '--tolerance 0.075',
            'shoreline.geojson',
        ])
    elif algo_interface == 'pzsvc-ndwi-py':
        band_flag = ''
        if scene_platform == scenes.PLATFORM_PLANETSCOPE:
            band_flag = '--bands 2 4'
        elif scene_platform == scenes.PLATFORM_RAPIDEYE:
            band_flag = '--bands 2 5'
        return ' '.join([
            ' '.join(['-i ' + filename for filename in geotiff_filenames]),
            band_flag,
            '--fout ./shoreline.geojson',
        ])
    else:
        error_message = 'unknown algorithm interface "' + algo_interface + '".'
        log.error(error_message)
        raise PreprocessingError(message=error_message)


def _resolve_detections_data_id(output_data_id: str) -> str:
    try:
        execution_output = piazza.get_file(output_data_id).json()
        return str(execution_output['OutFiles']['shoreline.geojson'])
    except piazza.Error as err:
        raise PostprocessingError(err, 'could not fetch execution output: {}'.format(err))
    except json.JSONDecodeError as err:
        raise PostprocessingError(err, 'malformed execution output: {}'.format(err))
    except KeyError as err:
        raise PostprocessingError(err, 'execution output is missing key `{}`'.format(err))


def _save_execution_error(job_id: str, execution_step: str, error_message: str, status: str = piazza.STATUS_ERROR):
    log = logging.getLogger(__name__)
    log.debug('<%s> updating database record', job_id)
    conn = db.get_connection()
    transaction = conn.begin()
    try:
        db.jobs.update_status(
            conn,
            job_id=job_id,
            status=status,
        )
        db.jobs.insert_job_failure(
            conn,
            job_id=job_id,
            execution_step=execution_step,
            error_message=error_message,
        )
        transaction.commit()
    except db.DatabaseError as err:
        transaction.rollback()
        log.error('<%s> database update failed', job_id)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()


def _serialize_dt(dt: datetime = None) -> str:
    if dt is not None:
        return dt.isoformat()


#
# Errors
#

class Error(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class NotFound(Error):
    def __init__(self, job_id: str):
        super().__init__('job `{}` not found'.format(job_id))
        self.job_id = job_id


class PostprocessingError(Error):
    def __init__(self, err: Exception = None, message: str = None):
        super().__init__('during postprocessing, {}'.format(message or err))


class PreprocessingError(Error):
    def __init__(self, err: Exception = None, message: str = None):
        super().__init__('during preprocessing, {}'.format(message or err))
