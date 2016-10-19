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

from aiohttp.web import json_response, Request, Response

from bfapi.logger import get_logger
from bfapi import piazza
from bfapi.routes import v0

_time_started = time.time()


async def health_check(request: Request):
    uptime = round(time.time() - _time_started, 3)
    return json_response({
        'uptime': uptime,
    })


async def login(request: Request):
    log = get_logger()

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return 'Authorization header is missing', 401

    try:
        token = piazza.create_session(auth_header)
    except piazza.MalformedSessionToken as err:
        return Response(status=400, text=err.message)
    except piazza.Unauthorized as err:
        return Response(status=401, text=err.message)
    except piazza.Error as err:
        log.error('Cannot log in: %s', err)
        return Response(status=500, text='A Piazza error prevents login')

    return json_response({
        'token': token,
    })
