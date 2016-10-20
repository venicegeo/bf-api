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

from bfapi import piazza
from bfapi.logger import get_logger


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
            url: str,
            version: str):
        self.bands = bands
        self.description = description
        self.interface = interface
        self.max_cloud_cover = max_cloud_cover
        self.name = name
        self.service_id = service_id
        self.url = url
        self.version = version

    def to_json(self):
        return {
            'bands': self.bands,
            'description': self.description,
            'interface': self.interface,
            'maxCloudCover': self.max_cloud_cover,
            'name': self.name,
            'serviceId': self.service_id,
            'url': self.url,
            'version': self.version,
        }


#
# Actions
#

def list_all(session_token: str) -> List[Algorithm]:
    log = get_logger()
    try:
        log.info('Querying Piazza for available beachfront algorithms')
        services = piazza.get_services(session_token, '^BF_Algo_')
    except piazza.Error as err:
        log.error('Service listing failed: %s', err)
        raise err

    algorithms = []
    for service in services:
        metadata = service.metadata.get('metadata')
        if not metadata:
            log.warning('Algorithm %s missing `metadata` hash', service.service_id)
            continue
        try:
            algorithm = Algorithm(
                bands=_extract_bands(service),
                interface=_extract_interface(service),
                description=_extract_description(service),
                max_cloud_cover=_extract_max_cloud_cover(service),
                name=_extract_name(service),
                service_id=service.service_id,
                url=_extract_url(service),
                version=_extract_version(service),
            )
            algorithms.append(algorithm)
        except ValidationError as err:
            log.error('Algorithm transformation failed: %s', err)
            continue
    return algorithms


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


def _extract_url(service: piazza.ServiceDescriptor) -> str:
    value = service.url.strip()
    if not value.startswith('https://'):
        raise ValidationError('algorithm `url` is not HTTPS')
    return value


def _extract_version(service: piazza.ServiceDescriptor) -> str:
    value = service.metadata.get('version')
    if not value:
        raise ValidationError('missing `version` requirement')
    return value.strip()


#
# Errors
#

class ValidationError(Exception):
    def __init__(self, message: str):
        super().__init__('invalid algorithm metadata: ' + message)
