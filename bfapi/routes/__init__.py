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

import flask

from bfapi.service import users
from bfapi.routes import v0

_time_started = time.time()


def health_check():
    uptime = round(time.time() - _time_started, 3)
    return flask.jsonify({
        'uptime': uptime,
    })


def is_login_active():
    """This should be mounted behind the verification middleware"""
    return '', 204


def login():
    query_params = flask.request.args

    try:
        auth_code = query_params['code'].strip()
    except:
        return 'Cannot log in: invalid "code" query parameter', 400

    try:
        user = users.authenticate_via_geoaxis(auth_code)
    except users.Unauthorized as err:
        return str(err), 401
    except users.GeoaxisUnreachable as err:
        return str(err), 503
    except users.Error:
        return 'Cannot log in: an internal error prevents authentication', 500

    return flask.jsonify({
        'api_key': user.api_key,
    })
