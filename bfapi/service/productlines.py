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

import hashlib
import json
import logging
import re
import time
from datetime import datetime
from typing import List, Tuple

from bfapi import piazza
from bfapi.config import DOMAIN, SYSTEM_API_KEY, PZ_GATEWAY, SKIP_PRODUCTLINE_INSTALL
from bfapi.db import jobs as jobs_db, productlines as productlines_db, get_connection, DatabaseError
from bfapi.service import algorithms as algorithms_service, jobs as jobs_service, scenes as scenes_service

HARVEST_EVENT_IDENTIFIER = 'beachfront:api:on_harvest_event'
FORMAT_ISO8601 = '%Y-%m-%dT%H:%M:%SZ'


#
# Types
#

class ProductLine:
    def __init__(
            self,
            *,
            productline_id: str,
            algorithm_name: str,
            bbox: dict,
            category: str = None,
            created_by: str,
            created_on: datetime,
            max_cloud_cover: int,
            name: str,
            owned_by: str,
            spatial_filter_id: str = None,
            start_on: datetime,
            stop_on: datetime):
        self.productline_id = productline_id
        self.algorithm_name = algorithm_name
        self.bbox = bbox
        self.category = category
        self.created_by = created_by
        self.created_on = created_on
        self.max_cloud_cover = max_cloud_cover
        self.name = name
        self.owned_by = owned_by
        self.spatial_filter_id = spatial_filter_id
        self.start_on = start_on
        self.stop_on = stop_on

    def serialize(self):
        return {
            'type': 'Feature',
            'id': self.productline_id,
            'geometry': self.bbox,
            'properties': {
                'algorithm_name': self.algorithm_name,
                'category': self.category,
                'created_by': self.created_by,
                'created_on': _serialize_dt(self.created_on),
                'max_cloud_cover': self.max_cloud_cover,
                'name': self.name,
                'owned_by': self.owned_by,
                'spatial_filter_id': self.spatial_filter_id,
                'start_on': _serialize_dt(self.start_on),
                'stop_on': _serialize_dt(self.stop_on),
            },
        }


#
# Actions
#

def create_event_signature():
    components = [
        SYSTEM_API_KEY,
        PZ_GATEWAY,
    ]
    return hashlib.sha384(':'.join(components).encode()).hexdigest()


def create_productline(
        *,
        api_key: str,
        algorithm_id: str,
        bbox: tuple,
        category: str,
        max_cloud_cover: int,
        name: str,
        spatial_filter_id: str,
        start_on: datetime,
        stop_on: datetime,
        user_id: str) -> ProductLine:
    log = logging.getLogger(__name__)
    algorithm = algorithms_service.get(api_key, algorithm_id)
    productline_id = _create_id()
    log.info('Creating product line <%s>', productline_id)
    conn = get_connection()
    try:
        productlines_db.insert_productline(
            conn,
            productline_id=productline_id,
            algorithm_id=algorithm_id,
            algorithm_name=algorithm.name,
            bbox=bbox,
            category=category,
            max_cloud_cover=max_cloud_cover,
            name=name,
            spatial_filter_id=spatial_filter_id,
            start_on=start_on,
            stop_on=stop_on,
            user_id=user_id,
        )
    except DatabaseError as err:
        log.error('Could not insert product line record')
        err.print_diagnostics()
        raise

    return ProductLine(
        productline_id=productline_id,
        algorithm_name=algorithm.name,
        bbox=_to_geometry(bbox),
        category=category,
        created_by=user_id,
        created_on=datetime.utcnow(),
        max_cloud_cover=max_cloud_cover,
        name=name,
        owned_by=user_id,
        spatial_filter_id=spatial_filter_id,
        start_on=start_on,
        stop_on=stop_on,
    )


def install_if_needed(handler_endpoint: str):
    log = logging.getLogger(__name__)
    api_key = SYSTEM_API_KEY

    if SKIP_PRODUCTLINE_INSTALL:
        log.info('Skipping installation of Piazza trigger and service')
        return

    log.info('Checking to see if catalog harvest event handlers installation is required')

    needs_installation = False
    try:
        if not piazza.get_services(api_key, pattern='^{}$'.format(HARVEST_EVENT_IDENTIFIER)):
            needs_installation = True
            log.info('Registering harvest event handler service with Piazza')
            piazza.register_service(
                api_key,
                url='https://bf-api.{}/{}'.format(DOMAIN, handler_endpoint.lstrip('/')),
                contract_url='https://{}'.format(DOMAIN),
                description='Beachfront handler for Scene Harvest Event',
                name=HARVEST_EVENT_IDENTIFIER,
            )

        if not piazza.get_triggers(api_key, HARVEST_EVENT_IDENTIFIER):
            needs_installation = True
            log.info('Registering harvest event trigger with Piazza')
            event_type_id = scenes_service.get_event_type_id()
            signature = create_event_signature()
            handler_service = piazza.get_services(api_key, pattern='^{}$'.format(HARVEST_EVENT_IDENTIFIER))[0]
            piazza.create_trigger(
                api_key,
                event_type_id=event_type_id,
                name=HARVEST_EVENT_IDENTIFIER,
                service_id=handler_service.service_id,
                data_inputs={
                    "body": {
                        "content": """{
                            "__signature__": "%s",
                            "scene_id": "$imageID",
                            "captured_on": "$acquiredDate",
                            "cloud_cover": $cloudCover,
                            "min_x": $minx,
                            "min_y": $miny,
                            "max_x": $maxx,
                            "max_y": $maxy
                        }""" % signature,
                        "type": "body",
                        "mimeType": "application/json",
                    },
                },
            )
    except piazza.Error as err:
        log.error('Piazza call failed: %s', err)
        raise

    if needs_installation:
        log.info('Installation complete!')
    else:
        log.info('Event handlers exist and will not be reinstalled')


def get_all() -> List[ProductLine]:
    conn = get_connection()
    try:
        cursor = productlines_db.select_all(conn)
    except DatabaseError as err:
        err.print_diagnostics()
        raise err
    productlines = []
    for row in cursor.fetchall():
        productlines.append(ProductLine(
            productline_id=row['productline_id'],
            algorithm_name=row['algorithm_name'],
            bbox=json.loads(row['bbox']),
            category=row['category'],
            created_by=row['created_by'],
            created_on=row['created_on'],
            max_cloud_cover=row['max_cloud_cover'],
            name=row['name'],
            owned_by=row['owned_by'],
            spatial_filter_id=row['spatial_filter_id'],
            start_on=row['start_on'],
            stop_on=row['stop_on'],
        ))
    return productlines


def handle_harvest_event(
        *,
        scene_id: str,
        signature,
        cloud_cover,
        min_x,
        min_y,
        max_x,
        max_y):
    log = logging.getLogger(__name__)

    # Fail fast if event is untrusted
    if not _is_valid_event_signature(signature):
        raise UntrustedEventError()

    # Find all interested productlines
    conn = get_connection()
    try:
        cursor = productlines_db.select_summary_for_scene(
            conn,
            cloud_cover=cloud_cover,
            min_x=min_x,
            min_y=min_y,
            max_x=max_x,
            max_y=max_y,
        )
    except DatabaseError as err:
        log.error('Database search for applicable product lines failed')
        err.print_diagnostics()
        raise

    rows = cursor.fetchall()
    log.info('<scene:%s> Found %d applicable product lines', scene_id, len(rows))

    if not rows:
        return 'Disregard'

    for row in rows:
        pl_id = row['productline_id']
        algorithm_id = row['algorithm_id']
        pl_name = row['name']
        owner_user_id = row['owned_by']

        existing_job_id = _find_existing_job_id_for_scene(scene_id, algorithm_id)
        if existing_job_id:
            _link_to_job(pl_id, existing_job_id)
            continue

        log.info('<scene:%s> Spawning job in product line <%s>', scene_id, pl_id)
        new_job = jobs_service.create_job(
            api_key=SYSTEM_API_KEY,
            job_name=_create_job_name(pl_name, scene_id),
            scene_id=scene_id,
            service_id=algorithm_id,
            user_id=owner_user_id,
        )
        _link_to_job(pl_id, new_job.job_id)

    return 'Accept'


def _is_valid_event_signature(signature: str):
    return signature == create_event_signature()


#
# Helpers
#

def _create_id() -> str:
    return hashlib.md5(str(time.time()).encode()).hexdigest()


def _create_job_name(productline_name: str, scene_id: str):
    return '/'.join([
        re.sub(r'\W+', '_', productline_name)[0:32],  # Truncate and normalize
        re.sub(r'^landsat:', '', scene_id),
    ]).upper()


def _find_existing_job_id_for_scene(scene_id: str, algorithm_id: str) -> str:
    log = logging.getLogger(__name__)
    log.debug('Searching for existing jobs for scene <%s> and algorithm <%s>', scene_id, algorithm_id)
    conn = get_connection()
    try:
        row = jobs_db.select_jobs_for_inputs(
            conn,
            scene_id=scene_id,
            algorithm_id=algorithm_id,
        ).fetchone()
    except DatabaseError as err:
        log.error('Job query failed')
        err.print_diagnostics()
        raise
    return row['job_id'] if row else None


def _link_to_job(productline_id: str, job_id: str):
    log = logging.getLogger(__name__)
    log.info('<%s> Linking to job <%s>', productline_id, job_id)
    conn = get_connection()
    try:
        productlines_db.insert_productline_job(
            conn,
            job_id=job_id,
            productline_id=productline_id,
        )
    except DatabaseError as err:
        log.error('Cannot link job and productline')
        err.print_diagnostics()
        raise


def _serialize_dt(dt: datetime = None) -> str:
    if dt is not None:
        return dt.strftime(FORMAT_ISO8601)


def _to_geometry(bbox: Tuple[float, float, float, float]) -> dict:
    min_x, min_y, max_x, max_y = bbox
    return {
        'type': 'Polygon',
        'coordinates': [[
            [min_x, min_y],
            [min_x, max_y],
            [max_x, max_y],
            [max_x, min_y],
            [min_x, min_y],
        ]]
    }

#
# Errors
#

class Error(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class EventValidationError(Error):
    def __init__(self, err: Exception = None, message: str = 'invalid event: {}'):
        super().__init__(message.format(err))


class UntrustedEventError(Error):
    def __init__(self):
        super().__init__('untrusted event')
