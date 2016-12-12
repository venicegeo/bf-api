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

import re

import flask
from flask_cors import CORS

from bfapi import config, db, middleware, routes, service, IS_DEBUG_MODE


def attach_routes(app: flask.Flask):
    app.before_request(middleware.force_https)
    app.before_request(middleware.verify_api_key)

    CORS(app, max_age=1200, origins=[
        re.compile(r'^https://.*\.geointservices\.io$'),
        re.compile(r'^https?://localhost:8080$'),
    ])

    # Public Endpoints
    app.add_url_rule('/', view_func=routes.health_check, methods=['GET'])
    app.add_url_rule('/login', view_func=routes.login, methods=['POST'])

    # Session heartbeat
    app.add_url_rule('/login/heartbeat', view_func=routes.is_login_active, methods=['GET'])

    # API v0
    app.add_url_rule('/v0/services', view_func=routes.v0.list_supporting_services, methods=['GET'])
    app.add_url_rule('/v0/algorithm', view_func=routes.v0.list_algorithms, methods=['GET'])
    app.add_url_rule('/v0/algorithm/<service_id>', view_func=routes.v0.get_algorithm, methods=['GET'])
    app.add_url_rule('/v0/job', view_func=routes.v0.create_job, methods=['POST'])
    app.add_url_rule('/v0/job', view_func=routes.v0.list_jobs, methods=['GET'])
    app.add_url_rule('/v0/job/<job_id>', view_func=routes.v0.get_job, methods=['GET'])
    app.add_url_rule('/v0/job/<job_id>', view_func=routes.v0.forget_job, methods=['DELETE'])
    app.add_url_rule('/v0/job/<job_id>.geojson', view_func=routes.v0.download_geojson, methods=['GET'])
    app.add_url_rule('/v0/job/by_scene/<scene_id>', view_func=routes.v0.list_jobs_for_scene, methods=['GET'])
    app.add_url_rule('/v0/job/by_productline/<productline_id>', view_func=routes.v0.list_jobs_for_productline, methods=['GET'])
    app.add_url_rule('/v0/productline', view_func=routes.v0.list_productlines, methods=['GET'])
    app.add_url_rule('/v0/productline', view_func=routes.v0.create_productline, methods=['POST'])
    app.add_url_rule('/v0/productline/<productline_id>', view_func=routes.v0.delete_productline, methods=['DELETE'])
    app.add_url_rule('/v0/scene/event/harvest', view_func=routes.v0.on_harvest_event, methods=['POST'])


def banner():
    configurations = []
    for key, value in sorted(config.__dict__.items()):
        if not key.isupper() or 'PASSWORD' in key:
            continue
        configurations.append('{key:>38} : {value}'.format(key=key, value=value))
    print(
        '-' * 80,
        '',
        'bf-api'.center(80),
        '~~~~~~'.center(80),
        '',
        *configurations,
        '',
        '-' * 80,
        sep='\n',
        flush=True
    )


def init(app):
    banner()
    config.validate()
    db.init()

    install_service_assets()
    attach_routes(app)
    start_background_tasks()


def install_service_assets():
    service.productlines.install_if_needed('/v0/scene/event/harvest')
    service.geoserver.install_if_needed()


def start_background_tasks():
    service.jobs.start_worker()


################################################################################

#
# Bootstrapping
#

server = flask.Flask(__name__)
init(server)

################################################################################
