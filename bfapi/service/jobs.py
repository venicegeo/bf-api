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

import requests

from bfapi import piazza
from bfapi.config import JOB_TTL, JOB_WORKER_INTERVAL, SYSTEM_API_KEY, TIDE_SERVICE
from bfapi.db import jobs as jobs_db, get_connection, DatabaseError
from bfapi.service import algorithms as algorithms_service, scenes as scenes_service

FORMAT_ISO8601 = '%Y-%m-%dT%H:%M:%SZ'
FORMAT_DTG = '%Y-%m-%d-%H-%M'
FORMAT_TIME = '%TZ'
STATUS_TIMED_OUT = 'Timed Out'

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
            detections_id: str = None,
            geometry: dict,
            job_id: str,
            name: str,
            scene_capture_date: datetime,
            scene_sensor_name: str,
            scene_id: str,
            status: str):
        self.algorithm_name = algorithm_name
        self.algorithm_version = algorithm_version
        self.created_by = created_by
        self.created_on = created_on
        self.detections_id = detections_id
        self.geometry = geometry
        self.job_id = job_id
        self.name = name
        self.scene_capture_date = scene_capture_date
        self.scene_sensor_name = scene_sensor_name
        self.scene_id = scene_id
        self.status = status

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
                'detections_data_id': self.detections_id,
                'name': self.name,
                'scene_capture_date': _serialize_dt(self.scene_capture_date),
                'scene_id': self.scene_id,
                'scene_sensor_name': self.scene_sensor_name,
                'status': self.status,
                'type': 'JOB',
            }
        }


#
# Actions
#

def create_job(
        api_key: str,
        user_id: str,
        scene_id: str,
        service_id: str,
        job_name: str) -> Job:
    log = logging.getLogger(__name__)

    # Fetch prerequisites
    try:
        algorithm = algorithms_service.get(api_key, service_id)
        scene = scenes_service.get(scene_id)
    except (algorithms_service.NotFound,
            algorithms_service.ValidationError,
            scenes_service.CatalogError,
            scenes_service.NotFound,
            scenes_service.ValidationError) as err:
        raise PreprocessingError(err)

    # Fetch tide info
    try:
        tide_current, tide_min, tide_max = _fetch_tide_prediction(scene)
    except TidePredictionError as err:
        raise PreprocessingError(err)

    # Determine GeoTIFF URLs
    geotiff_filenames = []
    geotiff_urls = []
    for key in algorithm.bands:
        geotiff_url = scene.bands.get(key)
        if not geotiff_url:
            raise PreprocessingError(message='Scene `{}` is missing band `{}`'.format(scene.id, key))
        geotiff_urls.append(geotiff_url)
        geotiff_filenames.append(key + '.TIF')

    # Dispatch to Piazza
    try:
        log.info('<scene:%s> dispatched to algorithm via Piazza', scene_id)
        job_id = piazza.execute(api_key, algorithm.service_id, {
            'body': {
                'content': json.dumps({
                    'pzAuthKey': piazza.to_auth_header(api_key),
                    'cmd': ' '.join([
                        'shoreline',
                        '--image ' + ','.join(geotiff_filenames),
                        '--projection geo-scaled',
                        '--threshold 0.5',
                        '--tolerance 0.075',
                        '--prop tideMin24H:{}'.format(tide_min or 'null'),
                        '--prop tideMax24H:{}'.format(tide_max or 'null'),
                        '--prop tideCurrent:{}'.format(tide_current or 'null'),
                        '--prop classification:Unclassified',
                        '--prop dataUsage:Not_to_be_used_for_navigational_or_targeting_purposes.',
                        'shoreline.geojson',
                    ]),
                    'inExtFiles': geotiff_urls,
                    'inExtNames': ['coastal.TIF', 'swir1.TIF'],
                    'outGeoJson': ['shoreline.geojson'],
                }),
                'type': 'body',
                'mimeType': 'application/json',
            },
        })
    except piazza.Error as err:
        log.error('Could not execute via Piazza: %s', err)
        raise err

    # Record the data
    log.debug('Saving job record <%s>', job_id)
    conn = get_connection()
    transaction = conn.begin()
    try:
        jobs_db.insert_job(
            conn,
            algorithm_id=algorithm.service_id,
            algorithm_name=algorithm.name,
            algorithm_version=algorithm.version,
            job_id=job_id,
            name=job_name,
            scene_id=scene_id,
            status=piazza.STATUS_RUNNING,
            user_id=user_id,
        )
        jobs_db.insert_job_user(
            conn,
            job_id=job_id,
            user_id=user_id,
        )
        transaction.commit()
    except DatabaseError as err:
        transaction.rollback()
        log.error('Could not save job to database: %s', err)
        err.print_diagnostics()
        raise

    return Job(
        algorithm_name=algorithm.name,
        algorithm_version=algorithm.version,
        created_by=user_id,
        created_on=datetime.utcnow(),
        geometry=scene.geometry,
        job_id=job_id,
        name=job_name,
        scene_capture_date=scene.capture_date,
        scene_sensor_name=scene.sensor_name,
        scene_id=scene_id,
        status=piazza.STATUS_RUNNING,
    )


def forget(user_id: str, job_id: str) -> None:
    conn = get_connection()
    if not jobs_db.exists(conn, job_id=job_id):
        raise NotFound(job_id)
    try:
        jobs_db.delete_job_user(conn, job_id=job_id, user_id=user_id)
    except DatabaseError as err:
        err.print_diagnostics()
        raise


def get(user_id: str, job_id: str) -> Job:
    conn = get_connection()
    row = jobs_db.select_job(conn, job_id=job_id).fetchone()
    if not row:
        return

    # Add job to user's tracked jobs list
    try:
        jobs_db.insert_job_user(conn, job_id=job_id, user_id=user_id)
    except DatabaseError as err:
        err.print_diagnostics()
        raise

    return Job(
        algorithm_name=row['algorithm_name'],
        algorithm_version=row['algorithm_version'],
        created_by=row['created_by'],
        created_on=row['created_on'],
        detections_id=row['detections_id'],
        geometry=json.loads(row['geometry']),
        job_id=row['job_id'],
        name=row['name'],
        scene_capture_date=row['scene_capture_date'],
        scene_sensor_name=row['scene_sensor_name'],
        scene_id=row['scene_id'],
        status=row['status'],
    )


def get_all(user_id: str) -> List[Job]:
    conn = get_connection()

    try:
        cursor = jobs_db.select_jobs_for_user(conn, user_id=user_id)
    except DatabaseError as err:
        err.print_diagnostics()
        raise

    jobs = []
    for row in cursor.fetchall():
        feature = Job(
            algorithm_name=row['algorithm_name'],
            algorithm_version=row['algorithm_version'],
            created_by=row['created_by'],
            created_on=row['created_on'],
            detections_id=row['detections_id'],
            geometry=json.loads(row['geometry']),
            job_id=row['job_id'],
            name=row['name'],
            scene_capture_date=row['scene_capture_date'],
            scene_sensor_name=row['scene_sensor_name'],
            scene_id=row['scene_id'],
            status=row['status'],
        )
        jobs.append(feature)

    return jobs


def get_by_productline(productline_id: str) -> List[Job]:
    conn = get_connection()

    try:
        cursor = jobs_db.select_jobs_for_productline(conn, productline_id=productline_id)
    except DatabaseError as err:
        err.print_diagnostics()
        raise

    jobs = []
    for row in cursor.fetchmany():
        jobs.append(Job(
            algorithm_name=row['algorithm_name'],
            algorithm_version=row['algorithm_version'],
            created_by=row['created_by'],
            created_on=row['created_on'],
            detections_id=row['detections_id'],
            geometry=json.loads(row['geometry']),
            job_id=row['job_id'],
            name=row['name'],
            scene_capture_date=row['scene_capture_date'],
            scene_sensor_name=row['scene_sensor_name'],
            scene_id=row['scene_id'],
            status=row['status'],
        ))
    return jobs


def get_by_scene(scene_id: str) -> List[Job]:
    conn = get_connection()

    try:
        cursor = jobs_db.select_jobs_for_scene(conn, scene_id=scene_id)
    except DatabaseError as err:
        err.print_diagnostics()
        raise err

    jobs = []
    for row in cursor.fetchmany():
        jobs.append(Job(
            algorithm_name=row['algorithm_name'],
            algorithm_version=row['algorithm_version'],
            created_by=row['created_by'],
            created_on=row['created_on'],
            detections_id=row['detections_id'],
            geometry=json.loads(row['geometry']),
            job_id=row['job_id'],
            name=row['name'],
            scene_capture_date=row['scene_capture_date'],
            scene_sensor_name=row['scene_sensor_name'],
            scene_id=row['scene_id'],
            status=row['status'],
        ))
    return jobs


def start_worker(
        api_key: str = SYSTEM_API_KEY,
        job_ttl: timedelta = JOB_TTL,
        interval: timedelta = JOB_WORKER_INTERVAL):
    global _worker
    log = logging.getLogger(__name__)
    log.info('Starting worker thread')
    _worker = Worker(api_key, job_ttl, interval)
    _worker.start()


def stop_worker():
    global _worker
    log = logging.getLogger(__name__)
    log.info('Stopping worker thread')
    _worker.terminate()
    _worker = None


#
# Worker
#

class Worker(threading.Thread):
    def __init__(self, api_key: str, job_ttl: timedelta, interval: timedelta):
        super().__init__()
        self._api_key = api_key
        self._job_ttl = job_ttl
        self._interval = interval
        self._terminated = False

    def terminate(self):
        self._terminated = True

    def run(self):
        log = logging.getLogger(__name__ + '.worker')
        next_run = datetime.utcnow()
        while not self._terminated:
            if next_run > datetime.utcnow():
                time.sleep(3)  # Allows for timely graceful shutdowns
                continue

            conn = get_connection()
            try:
                rows = jobs_db.select_summary_for_status(conn, status=piazza.STATUS_RUNNING).fetchall()
            except DatabaseError as err:
                log.error('Could not list running jobs: %s', err)
                err.print_diagnostics()
                raise
            finally:
                conn.close()

            # Schedule next cycle
            next_run = datetime.utcnow() + self._interval
            if not rows:
                log.info('Nothing to do; next run at %s', next_run.strftime(FORMAT_TIME))
            else:
                log.info('Begin cycle for %d records', len(rows))
                for i, row in enumerate(rows):
                    _update_status(self._api_key, row['job_id'], row['created_on'], self._job_ttl, i + 1)
                log.info('Cycle complete; next run at %s', next_run.strftime(FORMAT_TIME))

        log.info('Stopping')


def _update_status(
        api_key: str,
        job_id: str,
        created_on: datetime,
        job_ttl: timedelta,
        index: int):
    log = logging.getLogger(__name__)

    # Get latest status
    try:
        status = piazza.get_status(api_key, job_id)
    except piazza.Unauthorized:
        log.error('<%03d/%s> credentials rejected during polling!', index, job_id)
        return
    except (piazza.ServerError, piazza.Error) as err:
        if isinstance(err, piazza.ServerError) and err.status_code == 404:
            log.warning('<%03d/%s> Job not found', index, job_id)
            _save_execution_error(job_id, 'runtime:polling-for-status', 'Job not found')
            return
        else:
            log.error('<%03d/%s> call to Piazza failed: %s', index, job_id, err.message)
            return

    # Emit console feedback
    log.info('<%03d/%s> polled (%s)', index, job_id, status.status)

    # Determine appropriate action by status
    if status.status == piazza.STATUS_RUNNING:
        if datetime.utcnow() - created_on < job_ttl:
            return
        log.warning('<%03d/%s> appears to have stalled and will no longer be tracked', index, job_id)
        _save_execution_error(job_id, 'runtime:timed-out', 'Processing time exceeded', status=STATUS_TIMED_OUT)

    elif status.status == piazza.STATUS_SUCCESS:
        log.info('<%03d/%s> Resolving detections data ID (via <%s>)', index, job_id, status.data_id)
        try:
            detections_data_id = _resolve_detections_data_id(api_key, status.data_id)
        except PostprocessingError as err:
            log.error('<%03d/%s> could not resolve detections data ID %s', index, job_id, err)
            _save_execution_error(job_id, 'postprocessing:resolve-detections-data-id', str(err))
            return

        log.info('<%03d/%s> Fetching detections from Piazza', index, job_id)
        try:
            geojson_as_text = piazza.get_file(api_key, detections_data_id).text
        except piazza.Unauthorized:
            log.error('<%03d/%s> credentials rejected during file retrieval!', index, job_id)
            return
        except piazza.ServerError as err:
            log.error('<%03d/%s> could not fetch data ID <%s>: %s', index, job_id, detections_data_id, err)
            _save_execution_error(job_id, 'postprocessing:collect-geojson', 'Could not retrieve GeoJSON from Piazza')
            return

        log.info('<%03d/%s> Inserting detections into PostGIS (%0.1fMB)', index, job_id, len(geojson_as_text)/1024000)
        conn = get_connection()
        try:
            jobs_db.insert_detection(conn, job_id=job_id, feature_collection=geojson_as_text)
        except DatabaseError as err:
            err.print_diagnostics()
            _save_execution_error(job_id, 'postprocessing:collect-geojson', 'Could not insert GeoJSON to database')
            return

        _save_execution_success(job_id, detections_data_id)

    elif status.status == piazza.STATUS_ERROR:
        _save_execution_error(job_id, 'runtime:during-algorithm', 'Job failed during algorithm run')  # FIXME -- use heuristics to determine specifics here

    elif status.status == piazza.STATUS_CANCELLED:
        _save_execution_error(job_id, 'runtime:cancelled', 'Job was cancelled', status=piazza.STATUS_CANCELLED)


def _resolve_detections_data_id(api_key, output_data_id) -> str:
    try:
        execution_output = piazza.get_file(api_key, output_data_id).json()
        return str(execution_output['OutFiles']['shoreline.geojson'])
    except piazza.Error as err:
        raise PostprocessingError(err, 'could not fetch execution output: {}'.format(err))
    except json.JSONDecodeError as err:
        raise PostprocessingError(err, 'malformed execution output: {}'.format(err))
    except KeyError as err:
        raise PostprocessingError(err, 'execution output is missing key `{}`'.format(err))


#
# Helpers
#

def _fetch_tide_prediction(scene: scenes_service.Scene) -> (float, float, float):
    log = logging.getLogger(__name__)
    x, y = _get_centroid(scene.geometry['coordinates'])
    dtg = scene.capture_date.strftime(FORMAT_DTG)

    log.debug('Predict tide for centroid (%s, %s) at %s', x, y, dtg)
    try:
        response = requests.post('https://{}/tides'.format(TIDE_SERVICE), json={
            'locations': [{
                'lat': y,
                'lon': x,
                'dtg': dtg
            }]
        })
        response.raise_for_status()
    except requests.ConnectionError:
        raise TidePredictionError('service is unreachable')
    except requests.HTTPError as err:
        raise TidePredictionError('HTTP {}'.format(err.response.status_code))

    # Validate and extract the response
    try:
        (prediction,) = response.json()['locations']
        current_tide = round(float(prediction['results']['currentTide']), 12)
        min_tide = round(float(prediction['results']['maximumTide24Hours']), 12)
        max_tide = round(float(prediction['results']['minimumTide24Hours']), 12)
        return current_tide, min_tide, max_tide
    except (ValueError, TypeError):
        log.error('Malformed tide prediction response:')
        print('!' * 80)
        print('\nRAW RESPONSE\n')
        print(response.text)
        print('!' * 80)
    return None, None, None


def _get_bbox(polygon: list):
    (min_x, min_y) = (max_x, max_y) = polygon[0][0]
    for x, y in polygon[0]:
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, x)
    return min_x, min_y, max_x, max_y


def _get_centroid(polygon: list):
    min_x, min_y, max_x, max_y = _get_bbox(polygon)
    return (max_x + min_x) / 2, (max_y + min_y) / 2


def _save_execution_error(job_id: str, execution_step: str, error_message: str, status: str = piazza.STATUS_ERROR):
    log = logging.getLogger(__name__)
    log.debug('<%s> updating database record', job_id)
    conn = get_connection()
    transaction = conn.begin()
    try:
        jobs_db.update_status(
            conn,
            job_id=job_id,
            status=status,
        )
        jobs_db.insert_job_failure(
            conn,
            job_id=job_id,
            execution_step=execution_step,
            error_message=error_message,
        )
        transaction.commit()
    except DatabaseError as err:
        transaction.rollback()
        log.error('<%s> database update failed', job_id)
        err.print_diagnostics()
        raise


def _save_execution_success(job_id: str, detections_data_id: str):
    log = logging.getLogger(__name__)
    log.debug('<%s> updating database record', job_id)
    conn = get_connection()
    try:
        jobs_db.update_status(
            conn,
            job_id=job_id,
            status=piazza.STATUS_SUCCESS,
            data_id=detections_data_id,
        )
    except DatabaseError as err:
        log.error('<%s> database update failed', job_id)
        err.print_diagnostics()
        raise


def _serialize_dt(dt: datetime = None) -> str:
    if dt is not None:
        return dt.strftime(FORMAT_ISO8601)


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


class TidePredictionError(Error):
    def __init__(self, message: str):
        super().__init__(message='tide prediction failed: {}'.format(message))
