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
from typing import List

from bfapi.service import piazza


#
# Types
#

class Algorithm:
    def __init__(
            self,
            *,
            bands: tuple,
            description: str,
            interface: str,
            max_cloud_cover: int,
            name: str,
            service_id: str,
            version: str):
        self.bands = bands
        self.description = description
        self.interface = interface
        self.max_cloud_cover = max_cloud_cover
        self.name = name
        self.service_id = service_id
        self.version = version

    def serialize(self):
        return {
            'bands': self.bands,
            'description': self.description,
            'interface': self.interface,
            'max_cloud_cover': self.max_cloud_cover,
            'name': self.name,
            'service_id': self.service_id,
            'version': self.version,
        }


#
# Actions
#

def list_all() -> List[Algorithm]:
    log = logging.getLogger(__name__)
    try:
        log.info('Fetching beachfront services from Piazza')
        services = piazza.get_services('^BF_Algo_')
    except piazza.Error as err:
        log.error('Service discovery failed: %s', err)
        raise

    algorithms = []
    for service in services:
        if 'metadata' not in service.metadata:
            log.warning('Algorithm <%s> missing `metadata` hash', service.service_id)
            continue
        try:
            algorithms.append(Algorithm(
                bands=_extract_bands(service),
                interface=_extract_interface(service),
                description=_extract_description(service),
                max_cloud_cover=_extract_max_cloud_cover(service),
                name=_extract_name(service),
                service_id=service.service_id,
                version=_extract_version(service),
            ))
        except ValidationError as err:
            log.error('Algorithm conversion failed: %s', err)
            continue
    return algorithms


def get(service_id: str):
    log = logging.getLogger(__name__)
    try:
        log.info('Fetch beachfront service `%s` from Piazza', service_id)
        service = piazza.get_service(service_id)
    except piazza.ServerError as err:
        log.error('Service lookup failed: %s', err)
        if err.status_code == 404:
            raise NotFound(service_id)
        raise
    except piazza.Error as err:
        log.error('Service lookup failed: %s', err)
        raise
    if 'metadata' not in service.metadata:
        raise ValidationError('missing `metadata` hash')
    try:
        return Algorithm(
            bands=_extract_bands(service),
            interface=_extract_interface(service),
            description=_extract_description(service),
            max_cloud_cover=_extract_max_cloud_cover(service),
            name=_extract_name(service),
            service_id=service.service_id,
            version=_extract_version(service),
        )
    except ValidationError as err:
        log.error('Algorithm conversion failed: %s', err)
        raise


#
# Helpers
#

def _extract_bands(service: piazza.ServiceDescriptor) -> tuple:
    value = service.metadata['metadata'].get('ImgReq - bands')
    if not value:
        raise ValidationError('missing `bands` requirement')
    return tuple(s.strip().lower() for s in value.split(','))


def _extract_description(service: piazza.ServiceDescriptor) -> str:
    return service.description.strip() or 'No description'


def _extract_interface(service: piazza.ServiceDescriptor) -> str:
    value = service.metadata['metadata'].get('Interface')
    if not value:
        raise ValidationError('missing `Interface` specification')
    return value.strip().lower()


def _extract_max_cloud_cover(service: piazza.ServiceDescriptor) -> int:
    value = service.metadata['metadata'].get('ImgReq - cloudCover')
    if not value:
        raise ValidationError('missing `cloudCover` requirement')
    try:
        return int(value)
    except:
        raise ValidationError('`cloudCover` is not a number')


def _extract_name(service: piazza.ServiceDescriptor) -> str:
    return service.name.replace('BF_Algo_', '').strip()


def _extract_version(service: piazza.ServiceDescriptor) -> str:
    value = service.metadata.get('version')
    if not value:
        raise ValidationError('missing `version` requirement')
    return value.strip()


#
# Errors
#

class NotFound(Exception):
    def __init__(self, service_id: str):
        super().__init__('algorithm `{}` does not exist'.format(service_id))
        self.service_id = service_id


class ValidationError(Exception):
    def __init__(self, message: str):
        super().__init__('invalid algorithm metadata: ' + message)
