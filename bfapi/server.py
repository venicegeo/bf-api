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

import flask
from flask_cors import CORS

from bfapi import config, db, middleware, routes, service

FALLBACK_MIMETYPE = 'text/plain'


def attach_routes(app: flask.Flask):
    app.before_request(middleware.https_filter)
    app.before_request(middleware.csrf_filter)
    app.before_request(middleware.auth_filter)

    CORS(app,
         origins=middleware.AUTHORIZED_ORIGINS,
         max_age=1200,
         supports_credentials=True)

    # Public Endpoints
    app.add_url_rule(methods=['GET'], rule='/', view_func=routes.health_check)
    app.add_url_rule(methods=['GET'], rule='/login', view_func=routes.login)
    app.add_url_rule(methods=['GET'], rule='/login/start', view_func=routes.login_start)

    # Session heartbeat
    app.add_url_rule(methods=['GET'], rule='/login/heartbeat', view_func=routes.is_login_active)

    # API v0
    app.add_url_rule(methods=['GET'], rule='/v0/user', view_func=routes.v0.get_user_data)
    app.add_url_rule(methods=['GET'], rule='/v0/algorithm', view_func=routes.v0.list_algorithms)
    app.add_url_rule(methods=['GET'], rule='/v0/algorithm/<service_id>', view_func=routes.v0.get_algorithm)
    app.add_url_rule(methods=['POST'], rule='/v0/job', view_func=routes.v0.create_job)
    app.add_url_rule(methods=['GET'], rule='/v0/job', view_func=routes.v0.list_jobs)
    app.add_url_rule(methods=['GET'], rule='/v0/job/<job_id>', view_func=routes.v0.get_job)
    app.add_url_rule(methods=['DELETE'], rule='/v0/job/<job_id>', view_func=routes.v0.forget_job)
    app.add_url_rule(methods=['GET'], rule='/v0/job/<job_id>.geojson', view_func=routes.v0.download_geojson)
    app.add_url_rule(methods=['GET'], rule='/v0/job/by_scene/<scene_id>', view_func=routes.v0.list_jobs_for_scene)
    app.add_url_rule(methods=['GET'], rule='/v0/job/by_productline/<productline_id>', view_func=routes.v0.list_jobs_for_productline)
    app.add_url_rule(methods=['GET'], rule='/v0/productline', view_func=routes.v0.list_productlines)
    app.add_url_rule(methods=['POST'], rule='/v0/productline', view_func=routes.v0.create_productline)
    app.add_url_rule(methods=['DELETE'], rule='/v0/productline/<productline_id>', view_func=routes.v0.delete_productline)


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

    app.secret_key = config.SESSION_SECRET
    app.response_class.default_mimetype = FALLBACK_MIMETYPE

    install_service_assets()
    attach_routes(app)
    start_background_tasks()


def install_service_assets():
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
