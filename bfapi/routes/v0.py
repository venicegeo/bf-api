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

from json import JSONDecodeError

from aiohttp.web import Request, Response, json_response

from bfapi.db import DatabaseError
from bfapi.service import (algorithms as algorithms_service, jobs as jobs_service, productlines as productline_service)


#
# Algorithms
#

async def get_algorithm(request: Request):
    service_id = request.match_info['service_id']
    try:
        algorithm = algorithms_service.get(
            api_key=request['api_key'],
            service_id=service_id,
        )
    except algorithms_service.NotFound:
        return Response(status=404, text='Algorithm not found')
    return json_response({
        'algorithm': algorithm.serialize(),
    })


async def list_algorithms(request: Request):
    algorithms = algorithms_service.list_all(api_key=request['api_key'])
    return json_response({
        'algorithms': [algorithm.serialize() for algorithm in algorithms]
    })


#
# Jobs
#

async def create_job(request: Request):
    try:
        payload = await request.json()
        job_name = _get_string(payload, 'name', max_length=100)
        service_id = _get_string(payload, 'algorithm_id', max_length=64)
        scene_id = _get_string(payload, 'scene_id', max_length=64)
    except JSONDecodeError:
        return Response(status=400, text='Invalid input: request body must be a JSON object')
    except ValidationError as err:
        return Response(status=400, text='Invalid input: {}'.format(err))

    try:
        record = jobs_service.create_job(
            api_key=request['api_key'],
            user_id=request['username'],
            service_id=service_id,
            scene_id=scene_id,
            job_name=job_name.strip(),
        )
    except jobs_service.PreprocessingError as err:
        return Response(status=500, text='Cannot execute: {}'.format(err))
    except DatabaseError:
        return Response(status=500, text='A database error prevents job execution')
    return json_response(status=201, data=record.serialize())


async def forget_job(request: Request):
    job_id = request.match_info['job_id']
    try:
        jobs_service.forget(request['username'], job_id)
    except jobs_service.NotFound:
        return Response(status=404, text='Job not found')
    return Response(text='Forgot {}'.format(job_id))


async def list_jobs(request: Request):
    jobs = jobs_service.get_all(request['username'])
    return json_response({
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        },
    })


async def list_jobs_for_productline(request: Request):
    jobs = jobs_service.get_by_productline(request.match_info['productline_id'])
    return json_response({
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        }
    })


async def list_jobs_for_scene(request: Request):
    jobs = jobs_service.get_by_scene(request.match_info['scene_id'])
    return json_response({
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        }
    })


async def get_job(request: Request):
    record = jobs_service.get(request['username'], request.match_info['job_id'])
    if not record:
        return Response(status=404, text='Job not found')
    return json_response(record.serialize())


#
# Product Lines
#

async def on_harvest_event(request: Request):
    try:
        payload = await request.json()
        signature = _get_string(payload, '__signature__')
        scene_id = _get_string(payload, 'scene_id', max_length=64)
        cloud_cover = _get_number(payload, 'cloud_cover', min_value=0, max_value=100)
        min_x = _get_number(payload, 'min_x', min_value=-180, max_value=180)
        min_y = _get_number(payload, 'min_y', min_value=-90, max_value=90)
        max_x = _get_number(payload, 'max_x', min_value=-180, max_value=180)
        max_y = _get_number(payload, 'max_y', min_value=-90, max_value=90)
    except JSONDecodeError:
        return Response(status=400, text='Invalid input: request body must be a JSON object')
    except ValidationError as err:
        return Response(status=400, text='Invalid input: {}'.format(err))

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
        return Response(status=401, text='Error: Invalid event signature')
    except productline_service.EventValidationError as err:
        return Response(status=400, text='Error: Invalid scene event: {}'.format(err))
    except jobs_service.PreprocessingError as err:
        return Response(status=500, text='Error: Cannot spawn job: {}'.format(err))
    except DatabaseError:
        return Response(status=500, text='A database error prevents job execution')
    return Response(text=disposition)


async def list_productlines(request: Request):
    productlines = productline_service.get_all()
    return json_response({
        'product_lines': [p.serialize() for p in productlines],
    })


#
# Helpers
#

def _get_number(d: dict, key: str, *, fallback: int = 0, min_value: int = None, max_value: int = None):
    value = d.get(key, fallback)
    if not isinstance(value, int) and not isinstance(value, float):
        raise ValidationError('`{}` must be a number'.format(key))

    if min_value is not None and value < min_value or max_value is not None and value > max_value:
        raise ValidationError('`{}` must be a number between {} and {}'.format(key, min_value, max_value))

    return value


def _get_string(d: dict, key: str, *, fallback: str = '', min_length: int = 1, max_length: int = 256):
    value = d.get(key, fallback)
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
