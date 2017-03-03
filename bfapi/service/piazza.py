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

from typing import List
import logging
import requests
import time

from bfapi.config import PIAZZA, PIAZZA_API_KEY

STATUS_CANCELLED = 'Cancelled'
STATUS_CANCELLING = 'Cancelling'
STATUS_ERROR = 'Error'
STATUS_FAIL = 'Fail'
STATUS_PENDING = 'Pending'
STATUS_RUNNING = 'Running'
STATUS_SUBMITTED = 'Submitted'
STATUS_SUCCESS = 'Success'
TYPE_DATA = 'data'
TYPE_DEPLOYMENT = 'deployment'

TIMEOUT_LONG = 24
TIMEOUT_SHORT = 6


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
            service_id: str):
        self.description = description
        self.metadata = metadata
        self.name = name
        self.service_id = service_id


#
# Actions
#

def create_trigger(*, data_inputs: dict, event_type_id: str, name: str, service_id: str) -> str:
    log = logging.getLogger(__name__)
    log.info('Piazza service create trigger', action='service piazza create trigger')
    try:
        response = requests.post(
            'https://{}/trigger'.format(PIAZZA),
            timeout=TIMEOUT_LONG,
            auth=(PIAZZA_API_KEY, ''),
            json={
                'name': name,
                'eventTypeId': event_type_id,
                'condition': {
                    'query': {'query': {'match_all': {}}},
                },
                'job': {
                    'jobType': {
                        'type': 'execute-service',
                        'data': {
                            'serviceId': service_id,
                            'dataInputs': data_inputs,
                            'dataOutput': [{
                                'mimeType': 'text/plain',
                                'type': 'text'
                            }],
                        },
                    },
                },
                'enabled': True,
            },
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Connection failed: %s; url="%s"', err, err.request.url)
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise Unauthorized()
        raise ServerError(status_code)

    data = response.json().get('data')
    if not data:
        raise InvalidResponse('missing `data`', response.text)

    trigger_id = data.get('triggerId')
    if not trigger_id:
        raise InvalidResponse('missing `data.triggerId`', response.text)

    return trigger_id


def deploy(data_id: str, *, poll_interval: int = 3, max_poll_attempts: int = 10) -> str:
    log = logging.getLogger(__name__)
    log.info('Piazza service deploy', action='service piazza deploy')
    try:
        response = requests.post(
            'https://{}/deployment'.format(PIAZZA),
            timeout=TIMEOUT_LONG,
            auth=(PIAZZA_API_KEY, ''),
            json={
                'dataId': data_id,
                'deploymentType': 'geoserver',
                'type': 'access',
            },
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Connection failed: %s; url="%s"', err, err.request.url)
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
        status = get_status(job_id)

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


def execute(service_id: str, data_inputs: dict, data_output: list = None) -> str:
    log = logging.getLogger(__name__)
    log.info('Piazza service execute', action='service piazza execute')
    try:
        response = requests.post(
            'https://{}/job'.format(PIAZZA),
            timeout=TIMEOUT_LONG,
            auth=(PIAZZA_API_KEY, ''),
            headers={
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
            },
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Connection failed: %s; url="%s"', err, err.request.url)
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


def get_file(data_id: str) -> requests.Response:
    log = logging.getLogger(__name__)
    log.info('Piazza service get file', action='service piazza get file')
    try:
        response = requests.get(
            'https://{}/file/{}'.format(PIAZZA, data_id),
            timeout=TIMEOUT_LONG,
            auth=(PIAZZA_API_KEY, ''),
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Connection failed: %s; url="%s"', err, err.request.url)
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise Unauthorized()
        raise ServerError(status_code)
    return response


def get_service(service_id: str) -> ServiceDescriptor:
    log = logging.getLogger(__name__)
    log.info('Piazza service get service', action='service piazza get service')
    try:
        response = requests.get(
            'https://{}/service/{}'.format(PIAZZA, service_id),
            timeout=TIMEOUT_LONG,
            auth=(PIAZZA_API_KEY, ''),
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Connection failed: %s; url="%s"', err, err.request.url)
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


def get_services(pattern: str, count: int = 100) -> List[ServiceDescriptor]:
    log = logging.getLogger(__name__)
    log.info('Piazza service get service', action='service piazza get service')
    try:
        response = requests.get(
            'https://{}/service'.format(PIAZZA),
            timeout=TIMEOUT_LONG,
            auth=(PIAZZA_API_KEY, ''),
            params={
                'keyword': pattern,
                'perPage': count,
            },
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Connection failed: %s; url="%s"', err, err.request.url)
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


def get_status(job_id: str) -> Status:
    log = logging.getLogger(__name__)
    log.info('Piazza service get status', action='service piazza get status')
    try:
        response = requests.get(
            'https://{}/job/{}'.format(PIAZZA, job_id),
            timeout=TIMEOUT_LONG,
            auth=(PIAZZA_API_KEY, ''),
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Connection failed: %s; url="%s"', err, err.request.url)
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
    if status not in (STATUS_CANCELLED,
                      STATUS_CANCELLING,
                      STATUS_ERROR,
                      STATUS_FAIL,
                      STATUS_PENDING,
                      STATUS_RUNNING,
                      STATUS_SUBMITTED,
                      STATUS_SUCCESS):
        raise InvalidResponse('ambiguous value for `data.status`', response.text)

    if status == STATUS_SUCCESS:
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

    return Status(status)


def get_triggers(name: str) -> list:
    log = logging.getLogger(__name__)
    log.info('Piazza service get trigger', action='service piazza get trigger')
    try:
        response = requests.post(
            'https://{}/trigger/query'.format(PIAZZA),
            timeout=TIMEOUT_LONG,
            auth=(PIAZZA_API_KEY, ''),
            json={
                'query': {
                    'match': {
                        'name': name,
                    },
                },
            },
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Connection failed: %s; url="%s"', err, err.request.url)
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

    return data


def register_service(
        *,
        contract_url: str,
        description: str,
        method: str = 'POST',
        name: str,
        timeout: int = 60,
        url: str,
        version: str = '0.0') -> str:
    log = logging.getLogger(__name__)
    log.info('Piazza service register service', action='service piazza register service')
    try:
        response = requests.post(
            'https://{}/service'.format(PIAZZA),
            timeout=TIMEOUT_LONG,
            auth=(PIAZZA_API_KEY, ''),
            json={
                'url': url,
                'contractUrl': contract_url,
                'method': method,
                'timeout': timeout,
                'resourceMetadata': {
                    'name': name,
                    'description': description,
                    'version': version,
                    'classType': {
                        'classification': 'Unclassified',
                    },
                },
            },
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Connection failed: %s; url="%s"', err, err.request.url)
        raise Unreachable()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            raise Unauthorized()
        raise ServerError(status_code)

    data = response.json().get('data')
    if data is None:
        raise InvalidResponse('missing `data`', response.text)
    elif not isinstance(data, dict):
        raise InvalidResponse('`data` is of the wrong type', response.text)

    service_id = data.get('serviceId')
    if service_id is None:
        raise InvalidResponse('missing `data.serviceId`', response.text)
    elif not isinstance(service_id, str):
        raise InvalidResponse('`serviceId` is of the wrong type', response.text)

    return service_id


#
# Helpers
#

def _to_service_descriptor(datum: dict, response_text: str):
    metadata = datum.get('resourceMetadata')  # type: dict
    if not metadata:
        raise InvalidResponse('Missing `resourceMetadata`', response_text)
    metadata = metadata.copy()
    name = metadata.get('name')
    if not name:
        raise InvalidResponse('Missing `resourceMetadata.name`', response_text)
    description = metadata.get('description')
    if not description:
        raise InvalidResponse('Missing `resourceMetadata.description`', response_text)
    service_id = datum.get('serviceId')
    if not service_id:
        raise InvalidResponse('Missing `serviceId`', response_text)

    # Prune redundant properties
    metadata.pop('name')
    metadata.pop('description')
    return ServiceDescriptor(
        service_id=service_id,
        description=description,
        metadata=metadata,
        name=name,
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


class ServerError(Error):
    def __init__(self, status_code: int):
        super().__init__('Piazza server error (HTTP {})'.format(status_code))
        self.status_code = status_code


class Unauthorized(Error):
    def __init__(self):
        super().__init__('credentials rejected by Piazza')


class Unreachable(Error):
    def __init__(self):
        super().__init__('Piazza is unreachable')
