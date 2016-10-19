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

from aiohttp.web import Application, Request, Response

from bfapi import piazza
from bfapi.logger import get_logger

PUBLIC_ENDPOINTS = ('/', '/login')


async def create_session_validation_filter(app: Application, handler):
    async def validate_session(request: Request):
        log = get_logger()

        if request.path in PUBLIC_ENDPOINTS:
            log.debug('Allowing access to public endpoint')
            return await handler(request)

        log.debug('Verifying session')
        session_token = request.headers.get('Authorization')

        if session_token is None:
            return Response(status=400, text='Missing authorization header')

        try:
            log.debug('Attaching username to request context')
            request['username'] = piazza.get_username(session_token)
        except piazza.SessionExpired:
            return Response(status=401, text='Piazza session has expired')
        except piazza.ServerError as err:
            log.error('Cannot validate session: %s', err)
            return Response(status=500, text='A Piazza error prevents session validation')
        except piazza.MalformedSessionToken as err:
            log.error('Client passed malformed session token: %s', err)
            return Response(status=500, text='Cannot validate malformed session token')
        except Exception as err:
            log.exception('Cannot validate session: %s', err)
            return Response(status=500, text='A server error prevents session validation')
        return await handler(request)

    return validate_session
