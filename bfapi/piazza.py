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
from typing import List

import requests
import time

from bfapi.config import PZ_GATEWAY

PATTERN_VALID_SESSION_TOKEN = re.compile('^Basic \S+$')
STATUS_CANCELLED = 'Cancelled'
STATUS_SUCCESS = 'Success'
STATUS_RUNNING = 'Running'
STATUS_ERROR = 'Error'
TYPE_DATA = 'data'
TYPE_DEPLOYMENT = 'deployment'


#
# Types
#

class Status:
    def __init__(
            self,
            status: str,
            *,
            data_id: str = None,
            layer_id: str = None,
            error_message: str = None):
        self.status = status
        self.data_id = data_id
        self.error_message = error_message
        self.layer_id = layer_id


class ServiceDescriptor:
    def __init__(
            self,
            *,
            description: str,
            metadata: dict,
            name: str,
            service_id: str,
            url: str):
        self.description = description
        self.metadata = metadata
        self.name = name
        self.service_id = service_id
        self.url = url


#
# Actions
#

def create_session(auth_header: str):
    if not PATTERN_VALID_SESSION_TOKEN.match(auth_header):
        raise MalformedSessionToken()

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
            raise Unauthorized()
        raise ServerError(status_code)

    uuid = response.json().get('uuid')
    if not uuid:
        raise InvalidResponse('missing `uuid`', response.text)

    return 'Basic ' + base64.encodebytes((uuid + ':').encode()).decode().strip()


def deploy(session_token: str, data_id: str, *, poll_interval: int = 5, max_poll_attempts: int = 6):
    if not PATTERN_VALID_SESSION_TOKEN.match(session_token):
        raise MalformedSessionToken()

    try:
        response = requests.post(
            'https://{}/deployment'.format(PZ_GATEWAY),
            headers={
                'Authorization': session_token,
            },
            json={
                'dataId': data_id,
                'deploymentType': 'geoserver',
                'type': 'access',
            }
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise Unauthorized()
        raise ServerError(status_code)

    data = response.json().get('data')
    if not data:
        raise InvalidResponse('missing `data`', response.text)

    job_id = data.get('jobId')
    if not job_id:
        raise InvalidResponse('missing `jobId`', response.text)

    # Poll until complete
    poll_attempts = 0
    while True:
        status = get_status(session_token, job_id)

        if status.status == STATUS_SUCCESS:
            return status.layer_id

        elif status.status == STATUS_RUNNING:
            poll_attempts += 1
            if poll_attempts >= max_poll_attempts:
                raise DeploymentError('exhausted max poll attempts')
            time.sleep(poll_interval)
            continue

        if status.status == STATUS_ERROR:
            raise DeploymentError('deployment job failed')

        else:
            raise DeploymentError('unexpected deployment job status: ' + status.status)


def execute(session_token: str, service_id: str, data_inputs: dict, data_output: list = None) -> str:
    if not PATTERN_VALID_SESSION_TOKEN.match(session_token):
        raise MalformedSessionToken()

    try:
        response = requests.post(
            'https://{}/job'.format(PZ_GATEWAY),
            headers={
                'Authorization': session_token,
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
            raise Unauthorized()
        raise ServerError(status_code)

    data = response.json().get('data')
    if not data:
        raise InvalidResponse('missing `data`', response.text)

    job_id = data.get('jobId')
    if not job_id:
        raise InvalidResponse('missing `data.jobId`', response.text)

    return job_id


def get_service(session_token: str, service_id: str) -> ServiceDescriptor:
    if not PATTERN_VALID_SESSION_TOKEN.match(session_token):
        raise MalformedSessionToken()

    try:
        response = requests.get(
            'https://{}/service/{}'.format(PZ_GATEWAY, service_id),
            headers={
                'Authorization': session_token,
            },
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise Unauthorized()
        raise ServerError(status_code)

    datum = response.json().get('data')
    if datum is None:
        raise InvalidResponse('missing `data`', response.text)
    elif not isinstance(datum, dict):
        raise InvalidResponse('`data` is of the wrong type', response.text)

    return _to_service_descriptor(datum, response.text)


def get_services(session_token: str, pattern: str, count: int = 100) -> List[ServiceDescriptor]:
    if not PATTERN_VALID_SESSION_TOKEN.match(session_token):
        raise MalformedSessionToken()

    try:
        response = requests.get(
            'https://{}/service'.format(PZ_GATEWAY),
            headers={
                'Authorization': session_token,
            },
            params={
                'keyword': pattern,
                'perPage': count,
            }
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise Unauthorized()
        raise ServerError(status_code)

    data = response.json().get('data')
    if data is None:
        raise InvalidResponse('missing `data`', response.text)
    elif not isinstance(data, list):
        raise InvalidResponse('`data` is of the wrong type', response.text)

    return [_to_service_descriptor(datum, response.text) for datum in data]


def get_status(session_token: str, job_id: str) -> Status:
    if not PATTERN_VALID_SESSION_TOKEN.match(session_token):
        raise MalformedSessionToken()

    try:
        response = requests.get(
            'https://{}/job/{}'.format(PZ_GATEWAY, job_id),
            headers={
                'Authorization': session_token,
            }
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise Unauthorized()
        raise ServerError(status_code)

    data = response.json().get('data')
    if not data:
        raise InvalidResponse('missing `data`', response.text)

    status = data.get('status')
    if not status:
        raise InvalidResponse('missing `data.status`', response.text)

    # Status wrangling
    if status == STATUS_RUNNING:
        return Status(status)

    elif status == STATUS_SUCCESS:
        result = data.get('result')
        if not result:
            raise InvalidResponse('missing `data.result`', response.text)

        result_type = result.get('type')
        if not result_type:
            raise InvalidResponse('missing `data.result.type`', response.text)

        if result_type == TYPE_DATA:
            data_id = result.get('dataId')
            if not data_id:
                raise InvalidResponse('missing `data.result.dataId`', response.text)
            return Status(status, data_id=data_id)

        elif result_type == TYPE_DEPLOYMENT:
            deployment = result.get('deployment')
            if not deployment:
                raise InvalidResponse('missing `data.result.deployment`', response.text)
            layer_id = deployment.get('layer')
            if not layer_id:
                raise InvalidResponse('missing `data.result.deployment.layer`', response.text)
            return Status(status, layer_id=layer_id)

        else:
            raise InvalidResponse('unknown result type `{}`'.format(result_type), response.text)

    elif status == STATUS_ERROR:
        result = data.get('result')
        error_message = None
        if result:
            error_message = result.get('message')
        return Status(status, error_message=error_message)

    elif status == STATUS_CANCELLED:
        # TODO -- find out what this new status even means
        return Status(status)

    else:
        raise InvalidResponse('ambiguous value for `data.status`', response.text)


def get_username(session_token: str) -> str:
    if not PATTERN_VALID_SESSION_TOKEN.match(session_token):
        raise MalformedSessionToken()

    # Extract the UUID
    try:
        uuid = base64.decodebytes(session_token[6:].encode()).decode()[:-1]  # Drop trailing ':'
    except Exception as err:
        raise MalformedSessionToken(err)

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
# Helpers
#

def _to_service_descriptor(datum, response_text: str):
    metadata = datum.get('resourceMetadata')
    if not metadata:
        raise InvalidResponse('Missing `resourceMetadata`', response_text)
    name = metadata.get('name')
    if not name:
        raise InvalidResponse('Missing `resourceMetadata.name`', response_text)
    description = metadata.get('description')
    if not description:
        raise InvalidResponse('Missing `resourceMetadata.description`', response_text)
    service_id = datum.get('serviceId')
    if not service_id:
        raise InvalidResponse('Missing `serviceId`', response_text)
    url = datum.get('url')
    if not url:
        raise InvalidResponse('Missing `url`', response_text)

    # Prune redundant properties
    metadata.pop('name')
    metadata.pop('description')
    return ServiceDescriptor(
        service_id=service_id,
        description=description,
        metadata=metadata,
        name=name,
        url=url,
    )


#
# Errors
#

class Error(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DeploymentError(Error):
    def __init__(self, message: str, err: Exception = None):
        super().__init__('Piazza deployment error: ' + message)
        self.original_error = err


class ExecutionError(Error):
    def __init__(self, message: str, err: Exception = None):
        super().__init__('Piazza execution error: ' + message)
        self.original_error = err


class InvalidResponse(Error):
    def __init__(self, message: str, response_text: str):
        super().__init__('invalid Piazza response: ' + message)
        self.response_text = response_text


class MalformedSessionToken(Error):
    def __init__(self, err: Exception = None):
        message = 'malformed Piazza session token'
        if err:
            message += ' ({})'.format(err)
        super().__init__(message)
        self.original_error = err


class ServerError(Error):
    def __init__(self, status_code: int):
        super().__init__('Piazza server error (HTTP {})'.format(status_code))
        self.status_code = status_code


class SessionExpired(Error):
    def __init__(self):
        super().__init__('Piazza session expired')


class Unauthorized(Error):
    def __init__(self, message: str = 'Credentials rejected'):
        super().__init__('unauthorized to access Piazza: ' + message)


class Unreachable(Error):
    def __init__(self):
        super().__init__('Piazza is unreachable')
