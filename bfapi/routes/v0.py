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

from datetime import datetime
from json import JSONDecodeError

import dateutil.parser
import flask

from bfapi.config import CATALOG, GEOSERVER_HOST
from bfapi.db import DatabaseError
from bfapi.service import (algorithms as algorithms_service, jobs as jobs_service, productlines as productline_service)


#
# Algorithms
#

def get_algorithm(service_id: str):
    try:
        algorithm = algorithms_service.get(
            api_key=flask.request.api_key,
            service_id=service_id,
        )
    except algorithms_service.NotFound:
        return 'Algorithm not found', 404
    return flask.jsonify({
        'algorithm': algorithm.serialize(),
    })


def list_algorithms():
    algorithms = algorithms_service.list_all(api_key=flask.request.api_key)
    return flask.jsonify({
        'algorithms': [a.serialize() for a in algorithms],
    })


#
# Jobs
#

def create_job():
    try:
        payload = flask.request.get_json()
        job_name = _get_string(payload, 'name', max_length=100)
        service_id = _get_string(payload, 'algorithm_id', max_length=64)
        scene_id = _get_string(payload, 'scene_id', max_length=64)
    except JSONDecodeError:
        return 'Invalid input: request body must be a JSON object', 400
    except ValidationError as err:
        return 'Invalid input: {}'.format(err), 400

    try:
        record = jobs_service.create(
            api_key=flask.request.api_key,
            user_id=flask.request.username,
            service_id=service_id,
            scene_id=scene_id,
            job_name=job_name.strip(),
        )
    except jobs_service.PreprocessingError as err:
        return 'Cannot execute: {}'.format(err), 500
    except DatabaseError:
        return 'A database error prevents job execution', 500
    return flask.jsonify({'job': record.serialize()}), 201


def forget_job(job_id: str):
    try:
        jobs_service.forget(flask.request.username, job_id)
    except jobs_service.NotFound:
        return 'Job not found', 404
    return 'Forgot {}'.format(job_id), 200


def list_jobs():
    jobs = jobs_service.get_all(flask.request.username)
    return flask.jsonify({
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        },
    })


def list_jobs_for_productline(productline_id: str):
    jobs = jobs_service.get_by_productline(productline_id)
    return flask.jsonify({
        'productline_id': productline_id,
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        },
    })


def list_jobs_for_scene(scene_id: str):
    jobs = jobs_service.get_by_scene(scene_id)
    return flask.jsonify({
        'scene_id': scene_id,
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        }
    })


def get_job(job_id: str):
    record = jobs_service.get(flask.request.username, job_id)
    if not record:
        return 'Job not found', 404
    return flask.jsonify(record.serialize())


#
# Product Lines
#

def create_productline():
    try:
        payload = flask.request.get_json()
        algorithm_id = _get_string(payload, 'algorithm_id', max_length=100)
        category = _get_string(payload, 'category', nullable=True, max_length=64)
        min_x = _get_number(payload, 'min_x', min_value=-180, max_value=180)
        min_y = _get_number(payload, 'min_y', min_value=-90, max_value=90)
        max_x = _get_number(payload, 'max_x', min_value=-180, max_value=180)
        max_y = _get_number(payload, 'max_y', min_value=-90, max_value=90)
        max_cloud_cover = int(_get_number(payload, 'max_cloud_cover', min_value=0, max_value=100))
        name = _get_string(payload, 'name', max_length=100)
        spatial_filter_id = _get_string(payload, 'spatial_filter_id', nullable=True, max_length=64)
        start_on = _get_datetime(payload, 'start_on')
        stop_on = _get_datetime(payload, 'stop_on', nullable=True)
    except JSONDecodeError:
        return 'Invalid input: request body must be a JSON object', 400
    except ValidationError as err:
        return 'Invalid input: {}'.format(err), 400

    try:
        productline = productline_service.create_productline(
            api_key=flask.request.api_key,
            algorithm_id=algorithm_id,
            bbox=(min_x, min_y, max_x, max_y),
            category=category,
            max_cloud_cover=max_cloud_cover,
            name=name,
            spatial_filter_id=spatial_filter_id,
            start_on=start_on.date(),
            stop_on=stop_on.date() if stop_on else None,
            user_id=flask.request.username,
        )
    except algorithms_service.NotFound as err:
        return 'Algorithm {} does not exist'.format(err.service_id), 500
    except DatabaseError:
        return 'A database error prevents product line creation', 500
    return flask.jsonify({'product_line': productline.serialize()}), 201


def list_productlines():
    productlines = productline_service.get_all()
    return flask.jsonify({
        'product_lines': {
            'type': 'FeatureCollection',
            'features': [p.serialize() for p in productlines],
        },
    })


def on_harvest_event():
    try:
        payload = flask.request.get_json()
        signature = _get_string(payload, '__signature__')
        scene_id = _get_string(payload, 'scene_id', max_length=64)
        cloud_cover = _get_number(payload, 'cloud_cover', min_value=0, max_value=100)
        min_x = _get_number(payload, 'min_x', min_value=-180, max_value=180)
        min_y = _get_number(payload, 'min_y', min_value=-90, max_value=90)
        max_x = _get_number(payload, 'max_x', min_value=-180, max_value=180)
        max_y = _get_number(payload, 'max_y', min_value=-90, max_value=90)
    except JSONDecodeError:
        return 'Invalid input: request body must be a JSON object', 400
    except ValidationError as err:
        return 'Invalid input: {}'.format(err), 400

    try:
        disposition = productline_service.handle_harvest_event(
            signature=signature,
            scene_id=scene_id,
            cloud_cover=cloud_cover,
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
        )
    except productline_service.UntrustedEventError:
        return 'Error: Invalid event signature', 401
    except productline_service.EventValidationError as err:
        return 'Error: Invalid scene event: {}'.format(err), 400
    except jobs_service.PreprocessingError as err:
        return 'Error: Cannot spawn job: {}'.format(err), 500
    except DatabaseError:
        return 'A database error prevents job execution', 500
    return disposition


#
# Service Listing
#

def list_supporting_services():
    return flask.jsonify({
        'services': {
            'catalog': 'https://{}'.format(CATALOG),
            'wms_server': 'https://{}/geoserver/wms'.format(GEOSERVER_HOST),
        },
    })

#
# Helpers
#

def _get_datetime(d: dict, key: str, *, nullable: bool = False) -> datetime:
    if key not in d:
        raise ValidationError('`{}` is missing'.format(key))
    value = d.get(key)
    if nullable and not value:
        return None
    try:
        value = dateutil.parser.parse(value)
    except:
        raise ValidationError('`{}` must be a valid timestamp'.format(key))
    return value


def _get_number(d: dict, key: str, *, min_value: int = None, max_value: int = None):
    if key not in d:
        raise ValidationError('`{}` is missing'.format(key))
    value = d.get(key)
    if not isinstance(value, int) and not isinstance(value, float):
        raise ValidationError('`{}` must be a number'.format(key))
    if min_value is not None and value < min_value or max_value is not None and value > max_value:
        raise ValidationError('`{}` must be a number between {} and {}'.format(key, min_value, max_value))
    return value


def _get_string(d: dict, key: str, *, nullable: bool = False, min_length: int = 1, max_length: int = 256):
    if key not in d:
        raise ValidationError('`{}` is missing'.format(key))
    value = d.get(key)
    if nullable and value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError('`{}` must be a string'.format(key))
    value = value.strip()
    if len(value) > max_length or len(value) < min_length:
        raise ValidationError('`{}` must be a string of {}–{} characters'.format(key, min_length, max_length))
    return value


#
# Errors
#

class ValidationError(Exception):
    pass
