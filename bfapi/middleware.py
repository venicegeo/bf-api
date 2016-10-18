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

from logging import getLogger

from flask import g, request

from bfapi import piazza


def session_validation_filter() -> None:
    log = getLogger(__name__ + ':validate_session')

    session_token = request.headers.get('Authorization')
    if session_token is None:
        return 'Missing authorization header', 400

    try:
        g.username = piazza.get_username(session_token)
    except piazza.SessionExpired:
        return 'Piazza session has expired', 401
    except piazza.Error as err:
        log.error('Cannot validate session: %s', err)
        return 'A Piazza error prevents session validation', 500
    except Exception as err:
        log.exception('Cannot validate session: %s', err)
        return 'A server error prevents session validation', 500
