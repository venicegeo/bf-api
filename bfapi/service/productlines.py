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
import logging
import re

from bfapi.config import SYSTEM_API_KEY, PZ_GATEWAY
from bfapi.db import jobs as jobsdb, productlines as productlinedb, get_connection, DatabaseError
from bfapi.service import jobs as jobs_service


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
        cursor = productlinedb.select_summary_for_scene(
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
    log.info('<%s> Found %d applicable product lines', scene_id, len(rows))

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

        log.info('<%s> Spawning job in product line <%s>', scene_id, pl_id)
        new_job = jobs_service.create_job(
            api_key=SYSTEM_API_KEY,
            job_name=_create_job_name(pl_name, scene_id),
            scene_id=scene_id,
            service_id=algorithm_id,
            user_id=owner_user_id,
        )
        _link_to_job(pl_id, new_job.job_id)

    return 'Accept'


def create_event_signature():
    components = [
        SYSTEM_API_KEY,
        PZ_GATEWAY,
    ]
    return hashlib.sha384(':'.join(components).encode()).hexdigest()


def _is_valid_event_signature(signature: str):
    return signature == create_event_signature()


#
# Helpers
#

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
        row = jobsdb.select_jobs_for_inputs(
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
        productlinedb.insert_productline_job(
            conn,
            job_id=job_id,
            productline_id=productline_id,
        )
        conn.commit()
    except DatabaseError as err:
        log.error('Cannot link job and productline')
        err.print_diagnostics()
        raise


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
