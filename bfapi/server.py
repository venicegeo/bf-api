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

from aiohttp.web import Application, UrlDispatcher

from bfapi import config, db, middleware, routes, service, IS_DEBUG_MODE


def attach_routes(app: Application):
    router = app.router  # type: UrlDispatcher

    # Public Endpoints
    router.add_get('/', routes.health_check)
    router.add_get('/login', routes.login)

    # API v0
    router.add_get('/v0/services', routes.v0.list_supporting_services)
    router.add_get('/v0/algorithm', routes.v0.list_algorithms)
    router.add_get('/v0/algorithm/{service_id}', routes.v0.get_algorithm)
    router.add_post('/v0/job', routes.v0.create_job)
    router.add_get('/v0/job', routes.v0.list_jobs)
    router.add_get('/v0/job/{job_id}', routes.v0.get_job)
    router.add_delete('/v0/job/{job_id}', routes.v0.forget_job)
    router.add_get('/v0/job/by_scene/{scene_id}', routes.v0.list_jobs_for_scene)
    router.add_get('/v0/job/by_productline/{productline_id}', routes.v0.list_jobs_for_productline)
    router.add_get('/v0/productline', routes.v0.list_productlines)
    router.add_post('/v0/productline', routes.v0.create_productline)
    router.add_post('/v0/scene/event/harvest', routes.v0.on_harvest_event)


def banner(_: Application):
    configurations = []
    for key, value in sorted(config.__dict__.items()):
        if not key.isupper():
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


def init(_: Application):
    config.validate()
    db.init()


def install_service_assets(_: Application):
    service.productlines.install_if_needed('/v0/scene/event/harvest')
    service.geoserver.install_if_needed()


def start_background_tasks(_: Application):
    service.jobs.start_worker()


def stop_background_tasks(_):
    service.jobs.stop_worker()


def teardown(_: Application):
    print('  SERVER IS SHUTTING DOWN  '.center(80, '-'))
    db.cleanup()


################################################################################

#
# Bootstrapping
#

server = Application(
    middlewares=[middleware.create_verify_api_key_filter],
    debug=IS_DEBUG_MODE,
)

server.on_startup.append(banner)
server.on_startup.append(init)
server.on_startup.append(attach_routes)
server.on_startup.append(install_service_assets)
server.on_startup.append(start_background_tasks)
server.on_shutdown.append(teardown)
server.on_shutdown.append(stop_background_tasks)

################################################################################
