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

from aiohttp.web import Application, Request, Response

from bfapi import piazza

PUBLIC_ENDPOINTS = ('/', '/login')


async def create_verify_api_key_filter(_: Application, handler):
    async def verify_api_key(request: Request):
        log = logging.getLogger(__name__)

        if request.path in PUBLIC_ENDPOINTS:
            log.debug('Allowing access to public endpoint')
            return await handler(request)

        log.debug('Verifying auth header')
        auth_header = request.headers.get('Authorization')
        if auth_header is None:
            return Response(status=400, text='Missing authorization header')

        try:
            log.debug('Extracting API key from Auth header')
            api_key = piazza.to_api_key(auth_header)

            log.debug('Identifying user')
            username = piazza.verify_api_key(api_key)

            log.debug('Attaching username and API key to request context')
            request['username'] = username
            request['api_key'] = api_key
        except piazza.ApiKeyExpired:
            return Response(status=401, text='Your Piazza API key has expired')
        except piazza.ServerError as err:
            log.error('Cannot verify API key: %s', err)
            return Response(status=500, text='A Piazza error prevents API key verification')
        except piazza.MalformedCredentials as err:
            log.error('Client passed malformed API key: %s', err)
            return Response(status=500, text='Cannot verify malformed API key')
        except Exception as err:
            log.exception('Cannot verify API key: %s', err)
            return Response(status=500, text='An internal error prevents API key verification')
        return await handler(request)

    return verify_api_key
