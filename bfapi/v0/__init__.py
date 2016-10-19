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

from flask import Blueprint, g, jsonify, request

from bfapi.db import DatabaseError
from bfapi.service import jobs

blueprint = Blueprint('v0', __name__)


@blueprint.route('/job', methods=['POST'])
def create_job():
    request.get_json()

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
            user_id=g.username,

            # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
            algorithm=_Algorithm(),
            # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK

            scene_id='landsat:LC80110632016220LGN00',
            job_name='test job name'
        )
    except DatabaseError:
        return 'A database error prevents job execution', 500
    return jsonify(record)


@blueprint.route('/job/<job_id>', methods=['DELETE'])
def forget_job(job_id: str):
    try:
        jobs.forget(g.username, job_id)
    except jobs.NotExists:
        return 'Job {} does not exist'.format(job_id), 404
    return 'Forgot {}'.format(job_id), 200


@blueprint.route('/job')
def list_jobs():
    feature_collection = jobs.get_all(g.username)
    return jsonify(jobs=feature_collection)


@blueprint.route('/job/<job_id>')
def get_job(job_id: str):
    feature = jobs.get(g.username, job_id)
    if not feature:
        return 'Job not found', 404
    return jsonify(job=feature)


@blueprint.route('/productline')
def list_productlines():
    return jsonify(productLines=[])
