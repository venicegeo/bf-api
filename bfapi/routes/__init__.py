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

import logging
import time

import flask

from bfapi import piazza
from bfapi.routes import v0

_time_started = time.time()


def health_check():
    uptime = round(time.time() - _time_started, 3)
    return flask.jsonify({
        'uptime': uptime,
    })


def login():
    log = logging.getLogger(__name__)

    auth_header = flask.request.headers.get('Authorization')
    if not auth_header:
        return 'Authorization header is missing', 401

    try:
        api_key = piazza.create_api_key(auth_header)
    except piazza.MalformedCredentials as err:
        return err.message, 400
    except piazza.Unauthorized as err:
        return err.message, 401
    except piazza.Error as err:
        log.error('Cannot log in: %s', err)
        return 'A Piazza error prevents login', 500

    return flask.jsonify({
        'api_key': api_key,
    })
