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

from flask import Flask, jsonify, request

from bfapi import config, logger, piazza
from bfapi.middleware import session_validation_filter
from bfapi import v0

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

server = Flask(__name__)
logger.init(server)


#
# Attach Routing
#

@server.route('/')
def health_check():
    uptime = round(time.time() - _time_started, 3)
    return jsonify(uptime=uptime)


@server.route('/login')
def login():
    log = logger.get_logger()
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return 'Authorization header is missing', 401
    try:
        token = piazza.create_session(auth_header)
    except piazza.AuthenticationError as err:
        return err.message, 401
    except piazza.Error as err:
        log.error('Cannot log in: %s', err)
        return 'A Piazza error prevents login', 500
    return jsonify(token=token)


v0.blueprint.before_request(session_validation_filter)
server.register_blueprint(v0.blueprint, url_prefix='/v0')
