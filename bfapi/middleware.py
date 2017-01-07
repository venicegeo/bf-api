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

import flask

from bfapi.service import users

PUBLIC_ENDPOINTS = (
    '/',
    '/login',
    '/v0/scene/event/harvest',
)


def force_https():
    log = logging.getLogger(__name__)
    request = flask.request  # type: flask.Request
    log.debug('Enforcing HTTPS on endpoint `%s`', request.path)
    if not request.is_secure:
        return 'HTTPS is required', 400


def verify_api_key():
    log = logging.getLogger(__name__)

    request = flask.request  # type: flask.Request

    if request.path in PUBLIC_ENDPOINTS:
        log.debug('Allowing access to public endpoint `%s`', request.path)
        return

    if request.method == 'OPTIONS':
        log.debug('Allowing preflight request to endpoint `%s`', request.path)
        return

    api_key = request.authorization.get('username', '').strip()
    if not api_key:
        return 'Missing API key', 401

    try:
        log.debug('Attaching user to request context')
        request.user = users.authenticate_via_api_key(api_key)
    except users.Unauthorized as err:
        return str(err), 401
    except users.MalformedAPIKey:
        return 'Cannot authenticate request: API key is malformed', 400
    except users.Error:
        return 'Cannot authenticate request: an internal error prevents API key verification', 500
