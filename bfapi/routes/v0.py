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

from aiohttp.web import Request, Response, json_response

from bfapi.db import DatabaseError
from bfapi.service import jobs


async def create_job(request: Request):
    # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
    # Collect data
    class _Algorithm:
        def __init__(self):
            self.version = '13'
            self.url = 'https://pzsvc-ossim.stage.geointservices.io'
            self.name = 'NDWI'
            self.service_id = 'e786a7d6-30ee-42b2-bf2f-1bff99c790e1'
            self.bands = ('coastal', 'swir1')
    # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK

    try:
        record = jobs.create_job(
            auth_token=request.headers['Authorization'],
            user_id=request['username'],

            # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
            algorithm=_Algorithm(),
            # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK

            scene_id='landsat:LC80110632016220LGN00',
            job_name='test job name'
        )
    except DatabaseError:
        return Response(status=500, text='A database error prevents job execution')
    return json_response(record)


async def forget_job(request: Request):
    job_id = request.match_info['job_id']
    try:
        jobs.forget(request['username'], job_id)
    except jobs.NotExists:
        return Response(status=404, text='Job not found')
    return Response(text='Forgot {}'.format(job_id))


async def list_jobs(request: Request):
    feature_collection = jobs.get_all(request['username'])
    return json_response({
        'jobs': feature_collection,
    })


async def get_job(request: Request):
    record = jobs.get(request['username'], request.match_info['job_id'])
    if not record:
        return Response(status=404, text='Job not found')
    return json_response(record)


async def list_productlines(request: Request):
    return json_response({
        'productLines': [],
    })
