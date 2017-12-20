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

import json
import logging
import random
import re

from datetime import datetime, date
from typing import List, Tuple

from bfapi import db, service

FORMAT_ISO8601 = '%Y-%m-%dT%H:%M:%SZ'
STATUS_ACTIVE = 'Active'
STATUS_INACTIVE = 'Inactive'


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
            start_on: date,
            stop_on: date):
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

    @property
    def status(self):
        if not self.stop_on or date.today() <= self.stop_on:
            return STATUS_ACTIVE
        return STATUS_INACTIVE

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
                'status': self.status,
                'stop_on': _serialize_dt(self.stop_on),
                'type': 'PRODUCT_LINE',
            },
        }


#
# Actions
#

def create_productline(
        *,
        algorithm_id: str,
        bbox: tuple,
        category: str,
        max_cloud_cover: int,
        name: str,
        spatial_filter_id: str,
        start_on: date,
        stop_on: date,
        user_id: str) -> ProductLine:
    log = logging.getLogger(__name__)
    log.info('Productline service create productline', action='service productline create productline')
    algorithm = service.algorithms.get(algorithm_id)
    productline_id = _create_id()
    log.info('Creating product line <%s>', productline_id)
    conn = db.get_connection()
    try:
        db.productlines.insert_productline(
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
    except db.DatabaseError as err:
        log.error('Could not insert product line record')
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()

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


def delete_productline(user_id: str, productline_id: str) -> None:
    log = logging.getLogger(__name__)
    log.info('Productline service delete productline "%s"', productline_id, action='service productline delete productline')

    conn = db.get_connection()
    try:
        productline = db.productlines.select_productline(conn, productline_id=productline_id).fetchone()
        if not productline:
            raise NotFound(productline_id)

        if user_id != productline['owned_by']:
            raise PermissionError('only the owner can delete this productline')

        db.productlines.delete_productline(conn, productline_id=productline_id)
    except db.DatabaseError as err:
        log.error('Could not delete productline <%s>', productline_id)
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()


def get_all() -> List[ProductLine]:
    log = logging.getLogger(__name__)
    log.info('Productline service get all', action='service productline get all')

    conn = db.get_connection()
    try:
        cursor = db.productlines.select_all(conn)
    except db.DatabaseError as err:
        log.error('Could not list productlines')
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
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


#
# Helpers
#

def _create_id() -> str:
    return ''.join([chr(n) for n in random.sample(range(97, 122), 16)])

def _find_existing_job_id_for_scene(scene_id: str, algorithm_id: str) -> str:
    log = logging.getLogger(__name__)
    log.debug('Searching for existing jobs for scene <%s> and algorithm <%s>', scene_id, algorithm_id)
    conn = db.get_connection()
    try:
        job_id = db.jobs.select_jobs_for_inputs(
            conn,
            scene_id=scene_id,
            algorithm_id=algorithm_id,
        ).scalar()
    except db.DatabaseError as err:
        log.error('Job query failed')
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()
    return job_id


def _link_to_job(productline_id: str, job_id: str):
    log = logging.getLogger(__name__)
    log.info('<%s> Linking to job <%s>', productline_id, job_id)
    conn = db.get_connection()
    try:
        db.productlines.insert_productline_job(
            conn,
            job_id=job_id,
            productline_id=productline_id,
        )
    except db.DatabaseError as err:
        log.error('Cannot link job and productline')
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()


def _serialize_dt(dt: date = None) -> str:
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


class NotFound(Error):
    def __init__(self, productline_id: str):
        super().__init__('productline <{}> not found'.format(productline_id))
        self.productline_id = productline_id
