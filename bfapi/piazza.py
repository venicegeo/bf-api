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


def get_username(session_token: str) -> str:
    if not re.match(r'^Basic \S+$', session_token):
        raise AuthError('unsupported auth token')

    # Extract the UUID
    try:
        uuid = base64.decodebytes(session_token[6:].encode()).decode()[:-1]  # Drop trailing ':'
    except Exception as err:
        raise AuthError('could not parse auth token', err)

    # Verify with Piazza IDAM
    try:
        response = requests.post(
            'https://{}/v2/verification'.format(PZ_GATEWAY.replace('pz-gateway.', 'pz-idam.')),
            json={'uuid': uuid},
            timeout=5,
        )
    except requests.ConnectionError:
        raise AuthError('cannot reach Piazza')
    except requests.HTTPError:
        raise AuthError('upstream server error')

    # Validate the response
    auth = response.json()
    if not auth.get('authenticated'):
        raise SessionExpired()

    username = auth.get('username')
    if not username:
        raise InvalidResponseError(response.text, 'missing username')

    return username


def create_session_token(auth_header: str):
    if not re.match(r'^Basic \S+$', auth_header):
        raise AuthError('unsupported auth header')

    try:
        response = requests.get(
            'https://{}/key'.format(PZ_GATEWAY),
            headers={'Authorization': auth_header},
        )
    except requests.ConnectionError:
        raise AuthError('cannot reach Piazza')

    if response.status_code == 500:
        raise AuthError('upstream server failure')

    uuid = response.json().get('uuid', '')
    if not uuid or response.status_code == 401:
        raise AuthError('Credentials rejected')

    return 'Basic ' + base64.encodebytes((uuid + ':').encode()).decode().strip()


def execute(service_id: str, data_inputs: dict, data_output: list = None) -> str:
    requests.post(PZ_GATEWAY + '/job', {
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


class InvalidResponseError(Exception):
    def __init__(self, contents: str, message: str):
        super().__init__('InvalidResponseError: ' + message)
        self.contents = contents
        self.message = message


class AuthError(Exception):
    def __init__(self, message: str, err: Exception = None):
        super().__init__('AuthError: ' + message)
        self.message = message
        self.original_error = err


class SessionExpired(Exception):
    def __init__(self):
        super().__init__('SessionExpired')
