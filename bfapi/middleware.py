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

from bfapi import piazza

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

    log.debug('Verifying auth header')
    auth_header = request.headers.get('Authorization')
    if auth_header is None:
        return 'Missing authorization header', 400

    try:
        log.debug('Extracting API key from Auth header')
        api_key = piazza.to_api_key(auth_header)

        log.debug('Identifying user')
        username = piazza.verify_api_key(api_key)

        log.debug('Attaching username and API key to request context')
        request.username = username
        request.api_key = api_key
    except piazza.ApiKeyExpired:
        return 'Your Piazza API key has expired', 401
    except piazza.ServerError as err:
        log.error('Cannot verify API key: %s', err)
        return 'A Piazza error prevents API key verification', 500
    except piazza.MalformedCredentials as err:
        log.error('Client passed malformed API key: %s', err)
        return 'Cannot verify malformed API key', 400
    except Exception as err:
        log.exception('Cannot verify API key: %s', err)
        return 'An internal error prevents API key verification', 500
