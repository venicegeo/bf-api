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

import base64
import re

import requests

from bfapi.config import PZ_GATEWAY






#
# Actions
#

def create_session(auth_header: str):
    if not re.match(r'^Basic \S+$', auth_header):
        raise AuthenticationError('unsupported auth header')

    try:
        response = requests.get(
            'https://{}/key'.format(PZ_GATEWAY),
            headers={
                'Authorization': auth_header,
            },
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise AuthenticationError('credentials rejected')
        raise ServerError(status_code)

    uuid = response.json().get('uuid')
    if not uuid:
        raise InvalidResponse('missing `uuid`', response.text)

    return 'Basic ' + base64.encodebytes((uuid + ':').encode()).decode().strip()


def execute(auth_token: str, service_id: str, data_inputs: dict, data_output: list = None) -> str:
    try:
        response = requests.post(
            'https://{}/job'.format(PZ_GATEWAY),
            headers={
                'Authorization': auth_token,
                'Content-Type': 'application/json',
            },
            json={
                'type': 'execute-service',
                'data': {
                    'serviceId': service_id,
                    'dataInputs': data_inputs,
                    'dataOutput': data_output or [{
                        'mimeType': 'application/json',
                        'type': 'text'
                    }]
                },
            })
        response.raise_for_status()
    except requests.ConnectionError:
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise AuthenticationError('credentials rejected')
        raise ServerError(status_code)

    data = response.json().get('data')
    if not data:
        raise InvalidResponse('missing `data`', response.text)

    job_id = data.get('jobId')
    if not job_id:
        raise InvalidResponse('missing `data.jobId`', response.text)

    return job_id


def get_username(session_token: str) -> str:
    if not re.match(r'^Basic \S+$', session_token):
        raise AuthenticationError('unsupported auth token')

    # Extract the UUID
    try:
        uuid = base64.decodebytes(session_token[6:].encode()).decode()[:-1]  # Drop trailing ':'
    except Exception as err:
        raise AuthenticationError('could not parse auth token', err)

    # Verify with Piazza IDAM
    try:
        response = requests.post(
            'https://{}/v2/verification'.format(PZ_GATEWAY.replace('pz-gateway.', 'pz-idam.')),
            json={
                'uuid': uuid,
            },
            timeout=5,
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise Unreachable()
    except requests.HTTPError as err:
        raise ServerError(err.response.status_code)

    # Validate the response
    auth = response.json()
    if not auth.get('authenticated'):
        raise SessionExpired()

    username = auth.get('username')
    if not username:
        raise InvalidResponse('missing `username`', response.text)

    return username


#
# Errors
#

class Error(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AuthenticationError(Error):
    def __init__(self, message: str, err: Exception = None):
        super().__init__('Piazza authentication error: ' + message)
        self.original_error = err


class ExecutionError(Error):
    def __init__(self, message: str, err: Exception = None):
        super().__init__('Piazza execution error: ' + message)
        self.original_error = err


class InvalidResponse(Error):
    def __init__(self, message: str, response_text: str):
        super().__init__('Invalid Piazza response: ' + message)
        self.response_text = response_text


class ServerError(Error):
    def __init__(self, status_code: int):
        super().__init__('Piazza server error (HTTP {})'.format(status_code))
        self.status_code = status_code


class SessionExpired(Error):
    def __init__(self):
        super().__init__('Piazza session expired')


class Unreachable(Error):
    def __init__(self):
        super().__init__('Piazza is unreachable')
