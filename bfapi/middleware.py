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

from bfapi.config import DOMAIN
from bfapi.service import users

AUTHORIZED_ORIGINS = (
    'https://beachfront.' + DOMAIN,
    'http://localhost:8080',
)

PUBLIC_ENDPOINTS = (
    '/',
    '/login',
)


def auth_filter():
    log = logging.getLogger(__name__)
    request = flask.request

    if request.path in PUBLIC_ENDPOINTS:
        log.debug('Allowing access to public endpoint `%s`', request.path)
        return

    if request.method == 'OPTIONS':
        log.debug('Allowing preflight request to endpoint `%s`', request.path)
        return

    # Check session
    api_key = flask.session.get('api_key')

    # Check Authorization header
    if not api_key and request.authorization:
        api_key = request.authorization['username'].strip()

    if not api_key:
        return 'Missing API key', 400

    try:
        log.debug('Attaching user to request context')
        request.user = users.authenticate_via_api_key(api_key)
    except users.Unauthorized as err:
        return str(err), 401
    except users.MalformedAPIKey:
        return 'Cannot authenticate request: API key is malformed', 400
    except users.Error:
        return 'Cannot authenticate request: an internal error prevents API key verification', 500


def csrf_filter():
    """
    Basic protection against Cross-Site Request Forgery in accordance with OWASP
    recommendations.  This middleware uses heuristics to identify CORS requests
    and checks the origin of those against the list of allowed origins.

    Reference:
      https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)_Prevention_Cheat_Sheet
    """

    log = logging.getLogger(__name__)
    request = flask.request

    if request.path in PUBLIC_ENDPOINTS:
        log.debug('Allowing access to public endpoint `%s`', request.path)
        return

    # Explicitly allow...
    origin = request.headers.get('Origin')
    if origin in AUTHORIZED_ORIGINS:
        log.debug('Allowing CORS access to protected endpoint `%s` from authorized origin `%s`', request.path, origin)
        return
    elif not origin and not request.referrer:
        log.debug('Allowing non-CORS access to protected endpoint `%s`', request.path)
        return

    # ...and reject everything else
    error_description = 'Possible CSRF attempt from unknown origin'
    if not origin and request.referrer:
        # This can be the case with <script src="http://bf-api/v0/job"></script>
        # which is not a legitimate usage of the Beachfront API
        error_description = 'Possible CSRF attempt via <script/> tag'

    log.warning('%s: endpoint=`%s` origin=`%s` referrer=`%s` ip=`%s`',
                error_description,
                request.path,
                origin,
                request.referrer,
                request.remote_addr)
    return 'Access Denied: CORS request validation failed', 403


def https_filter():
    log = logging.getLogger(__name__)
    request = flask.request

    if request.is_secure:
        log.debug('Allowing HTTPS request: endpoint=`%s` referrer=`%s`', request.path, request.referrer)
        return

    log.warning('Rejecting non-HTTPS request: endpoint=`%s` referrer=`%s`',
                request.path,
                request.referrer)
    return 'Access Denied: Please retry with HTTPS', 403
