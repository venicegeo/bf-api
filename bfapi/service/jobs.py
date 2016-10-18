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
from datetime import datetime
from logging import getLogger

import dateutil.parser
import requests

from bfapi import piazza
import bfapi.service.scenes as scenes_service
from bfapi.db import jobs as jobs_db, scenes as scenes_db, get_connection, DatabaseError

STATUS_RUNNING = 'Running'
STATUS_SUCCESS = 'Success'
STATUS_ERROR = 'Error'

FORMAT_ISO8601 = '%Y-%m-%dT%H:%M:%SZ'
FORMAT_DTG = '%Y-%m-%d-%H-%M'


def create_job(user_id, algorithm, scene_id, job_name) -> dict:
    log = getLogger(__name__ + ':create_job')

    # Fetch scene metadata
    scene = scenes_service.fetch(scene_id)

    # Fetch tide info
    tide_current, tide_min, tide_max = _fetch_tide_prediction(scene.geometry)

    # Determine GeoTIFF URLs
    geotiff_filenames = []
    geotiff_urls = []
    for key in algorithm.bands:
        geotiff_url = scene.bands.get(key)
        if not geotiff_url:
            raise ExecutionError(message='Scene `{}` is missing band `{}`'.format(scene['id'], key))
        geotiff_urls.append(geotiff_url)
        geotiff_filenames.append(key + '.TIF')

    # Serialize inputs
    geotiff_urls = ','.join(geotiff_urls)
    geotiff_filenames = ','.join(geotiff_filenames)

    try:
        log.info('<scene:%s> dispatch to Piazza', scene_id)
        job_id = piazza.execute(algorithm.service_id, {
            'authKey': {
                'content': '{{PZ_AUTH_KEY}}',
                'type': 'urlparameter'
            },
            'cmd': {
                'content': ' '.join([
                    'shoreline',
                    '--image ' + geotiff_filenames,
                    '--projection geo-scaled',
                    '--threshold 0.5',
                    '--tolerance 0.2',
                    '--prop 24hrMinTide:{:0.12}'.format(tide_min),
                    '--prop 24hrMaxTide:{:0.12}'.format(tide_max),
                    '--prop currentTide:{:0.12}'.format(tide_current),
                    '--prop classification:Unclassified',
                    '--prop dataUsage:Not_to_be_used_for_navigational_or_targeting_purposes.',
                    'shoreline.geojson',
                ]),
                'type': 'urlparameter'
            },
            'inFileURLs': {
                'content': geotiff_urls,
                'type': 'urlparameter'
            },
            'inExtFileNames': {
                'content': geotiff_filenames,
                'type': 'urlparameter'
            },
            'outGeoJson': {
                'content': 'shoreline.geojson',
                'type': 'urlparameter'
            }
        })
    except piazza.InvalidResponseError as err:
        log.error('Could not execute via Piazza: %s', err)
        raise err

    # Record the data
    conn = get_connection()
    try:
        scenes_db.insert(
            conn,
            scene_id,
            scene.capture_date,
            scene.uri,
            scene.cloud_cover,
            scene.geometry,
            scene.resolution,
            scene.sensor_name,
        )
        jobs_db.insert_job(
            conn,
            job_id,
            algorithm.name,
            algorithm.version,
            job_name,
            scene_id,
            STATUS_RUNNING,
        )
        jobs_db.insert_job_user(
            conn,
            job_id,
            user_id,
        )
        conn.commit()
    except DatabaseError as err:
        conn.rollback()
        log.exception('Could not save job to database: %s', err)
        raise err

    return _to_feature(
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
        status=STATUS_RUNNING,
    )


def get(user_id: str, job_id: str) -> dict:
    conn = get_connection()
    row = jobs_db.select_job(conn, job_id).fetchone()
    if not row:
        return

    # Add job to user's tracked jobs list
    try:
        jobs_db.insert_job_user(conn, job_id, user_id)
        conn.commit()
    except DatabaseError as err:
        conn.rollback()
        raise err

    return _to_feature(
        algorithm_name=row['algorithm_name'],
        algorithm_version=row['algorithm_version'],
        created_by=row['created_by'],
        created_on=dateutil.parser.parse(row['created_on']),
        detections_id=row['detections_id'],
        geometry=row['geometry'],
        job_id=row['job_id'],
        name=row['name'],
        scene_capture_date=dateutil.parser.parse(row['scene_capture_date']),
        scene_sensor_name=row['scene_sensor_name'],
        scene_id=row['scene_id'],
        status=row['status'],
    )


def get_all(user_id: str) -> dict:
    conn = get_connection()
    cursor = jobs_db.select_jobs_for_user(conn, user_id)

    feature_collection = {
        'type': 'FeatureCollection',
        'features': []
    }
    for row in cursor.fetchall():
        feature = _to_feature(
            algorithm_name=row['algorithm_name'],
            algorithm_version=row['algorithm_version'],
            created_by=row['created_by'],
            created_on=dateutil.parser.parse(row['created_on']),
            detections_id=row['detections_id'],
            geometry=row['geometry'],
            job_id=row['job_id'],
            name=row['name'],
            scene_capture_date=dateutil.parser.parse(row['scene_capture_date']),
            scene_sensor_name=row['scene_sensor_name'],
            scene_id=row['scene_id'],
            status=row['status'],
        )
        feature_collection['features'].append(feature)

    return feature_collection


#
# Helpers
#

def _fetch_tide_prediction(geometry: dict):
    # centroid = _get_centroid(geometry['coordinates'])
    # TODO -- implement
    min_tide = 0
    max_tide = 0
    current_tide = 0
    return current_tide, min_tide, max_tide


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


def _serialize_dt(dt: datetime = None) -> str:
    if dt is not None:
        return dt.strftime(FORMAT_ISO8601)


def _to_feature(
        algorithm_name: str = None,
        algorithm_version: str = None,
        created_by: str = None,
        created_on: datetime = None,
        detections_id: str = None,
        geometry: str = None,
        job_id: str = None,
        name: str = None,
        scene_capture_date: datetime = None,
        scene_sensor_name: str = None,
        scene_id: str = None,
        status: str = None,
) -> dict:
    return {
        'type': 'Feature',
        'id': job_id,
        'geometry': json.loads(geometry),
        'properties': {
            'algorithmName': algorithm_name,
            'algorithmVersion': algorithm_version,
            'createdBy': created_by,
            'createdOn': _serialize_dt(created_on),
            'detectionsDataId': detections_id,
            'name': name,
            'sceneCaptureDate': _serialize_dt(scene_capture_date),
            'sceneId': scene_id,
            'sceneSensorName': scene_sensor_name,
            'status': status,
            'type': 'JOB',
        }
    }


class ExecutionError(Exception):
    def __init__(self, err: Exception = None, message=None):
        if not message:
            (message,) = err.args
        super(message)
        self.message = message
        self.original_error = err

    def __str__(self):
        return 'ExecutionError: {}'.format(self.message)
