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
import re

import flask

from bfapi.service import users

PATTERNS_AUTHORIZED_ORIGINS = (
    re.compile(r'^https://beachfront(\.[^.]+)*\.geointservices\.io$'),
    re.compile(r'^https://bf-swagger(\.[^.]+)*\.geointservices\.io$'),
    re.compile(r'^https://localhost:8080$'),
)

PATTERNS_PUBLIC_ENDPOINTS = (
    re.compile(r'^/$'),
    re.compile(r'^/favicon.ico$'),
    re.compile(r'^/login$'),
    re.compile(r'^/login/geoaxis$'),
    re.compile(r'^/v0/scene/[^/]+$'),
)

ENDPOINTS_DO_NOT_EXTEND_SESSION = ['/v0/job', '/v0/productline']


def apply_default_response_headers(response: flask.Response) -> flask.Response:
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-XSS-Protection', '1; mode-block')
    response.headers.setdefault('Cache-Control', 'no-cache, no-store, must-revalidate, private')
    return response


def auth_filter():
    log = logging.getLogger(__name__)
    request = flask.request

    if _is_public_endpoint(request.path):
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
        return 'Cannot authenticate request: API key is missing', 401

    try:
        log.debug('Attaching user to request context')
        request.user = users.authenticate_via_api_key(api_key)
        log.info('User "%s" successfully authenticated request to endpoint "%s"', request.user.name, request.path)
    except users.Unauthorized as err:
        return str(err), 401
    except users.MalformedAPIKey:
        return 'Cannot authenticate request: API key is malformed', 401
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

    if _is_public_endpoint(request.path):
        log.debug('Allowing access to public endpoint `%s`', request.path)
        return

    # Explicitly allow...

    is_xhr = request.is_xhr or 'x-requested-with' in request.headers.get('Access-Control-Request-Headers', '').lower()
    origin = request.headers.get('Origin')
    if _is_authorized_origin(origin) and is_xhr:
        log.debug('Allowing CORS access to protected endpoint `%s` from authorized origin `%s`', request.path, origin)
        return
    elif not origin and not request.referrer:
        log.debug('Allowing non-CORS access to protected endpoint `%s`', request.path)
        return

    # ...and reject everything else
    log.warning('Possible CSRF attempt: endpoint=`%s` origin=`%s` referrer=`%s` ip=`%s` is_xhr=`%s`',
                request.path,
                origin,
                request.referrer,
                request.remote_addr,
                is_xhr)
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


#
# Helpers
#

def _is_authorized_origin(origin: str) -> bool:
    if not origin:
        return False
    for pattern in PATTERNS_AUTHORIZED_ORIGINS:
        if pattern.match(origin):
            return True
    return False


def _is_public_endpoint(path: str) -> bool:
    for pattern in PATTERNS_PUBLIC_ENDPOINTS:
        if re.match(pattern, path):
            return True
    return False
