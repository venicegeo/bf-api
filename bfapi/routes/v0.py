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
from bfapi.service import algorithms as algorithms_service, jobs as jobs_service


#
# Algorithms
#

async def get_algorithm(request: Request):
    service_id = request.match_info['service_id']
    try:
        algorithm = algorithms_service.get(
            session_token=request.headers['Authorization'],
            service_id=service_id,
        )
    except algorithms_service.NotFound:
        return Response(status=404, text='Algorithm not found')
    return json_response({
        'algorithm': algorithm.serialize(),
    })


async def list_algorithms(request: Request):
    algorithms = algorithms_service.list_all(session_token=request.headers['Authorization'])
    return json_response({
        'algorithms': [algorithm.serialize() for algorithm in algorithms]
    })


#
# Jobs
#

async def create_job(request: Request):
    session_token = request.headers['Authorization']

    try:
        payload = await request.json()
    except JSONDecodeError:
        return Response(status=400, text='Invalid input: request body must be a JSON object')

    job_name = payload.get('name')
    if not isinstance(job_name, str):
        return Response(status=400, text='Invalid input: `name` must be a string')

    service_id = payload.get('algorithmId')
    if not service_id:
        return Response(status=400, text='Invalid input: `algorithmId` must be a non-empty string')

    scene_id = payload.get('sceneId')
    if not scene_id:
        return Response(status=400, text='Invalid input: `sceneId` must be a non-empty string')

    try:
        record = jobs_service.create_job(
            session_token=session_token,
            user_id=request['username'],
            service_id=service_id,
            scene_id=scene_id,
            job_name=job_name.strip(),
        )
    except jobs_service.PreprocessingError as err:
        return Response(status=500, text='Cannot execute: {}'.format(err))
    except DatabaseError:
        return Response(status=500, text='A database error prevents job execution')
    return json_response(status=201, data=record)


async def forget_job(request: Request):
    job_id = request.match_info['job_id']
    try:
        jobs_service.forget(request['username'], job_id)
    except jobs_service.NotFound:
        return Response(status=404, text='Job not found')
    return Response(text='Forgot {}'.format(job_id))


async def list_jobs(request: Request):
    feature_collection = jobs_service.get_all(request['username'])
    return json_response({
        'jobs': feature_collection,
    })


async def get_job(request: Request):
    record = jobs_service.get(request['username'], request.match_info['job_id'])
    if not record:
        return Response(status=404, text='Job not found')
    return json_response(record)


#
# Product Lines
#

async def list_productlines(request: Request):
    return json_response({
        'productLines': [],
    })
