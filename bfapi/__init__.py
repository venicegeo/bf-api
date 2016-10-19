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

import time

from aiohttp.web import Application

from bfapi import config, logger, routes
from bfapi.middleware import create_session_validation_filter
from bfapi.service.jobs import start_worker as start_jobs_worker

_time_started = time.time()

################################################################################
# Debugging Info
print('-' * 80)
print()
print('bf-api'.center(80))
print('~~~~~~'.center(80))
print()
for key, value in sorted(config.__dict__.items()):
    if not key.isupper():
        continue
    print('{0:>38} : {1}'.format(key, value))
print()
print('-' * 80)
################################################################################

#
# Configuration
#

logger.init(config.DEBUG_MODE)
server = Application(
    middlewares=[create_session_validation_filter],
    debug=config.DEBUG_MODE
)


#
# Start Background Processes
#

server.on_startup.append(start_jobs_worker)

#
# Attach Routing
#

resource = server.router.add_resource
server.router.add_get('/', routes.health_check)
server.router.add_get('/login', routes.login)

# API v0
server.router.add_post('/v0/job', routes.v0.create_job)
server.router.add_get('/v0/job', routes.v0.list_jobs)
server.router.add_get('/v0/job/{job_id}', routes.v0.get_job)
server.router.add_delete('/v0/job/{job_id}', routes.v0.forget_job)
server.router.add_get('/v0/productline', routes.v0.list_productlines)
