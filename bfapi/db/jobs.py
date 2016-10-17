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
from sqlite3 import Connection, Cursor, OperationalError

from bfapi.db import DatabaseError


def insert_job(conn: Connection,
               job_id: str,
               algorithm_name: str,
               algorithm_version: int,
               name: str,
               scene_id: str,
               status: str):
    log = getLogger(__name__ + ':insert_job')
    try:
        log.debug('<%s>', job_id)
        conn.execute(
            """
            INSERT INTO job (id, algorithm_name, algorithm_version, created_by, detections_id, name, scene_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                algorithm_name,
                algorithm_version,
                name,
                scene_id,
                status,
            ))
    except OperationalError as err:
        log.exception('Failed %s', err)
        raise DatabaseError(err)


def insert_job_user(conn: Connection, job_id: str, user_id: str) -> None:
    log = getLogger(__name__ + ':insert_job_user')
    try:
        log.debug('<%s>', job_id)
        conn.execute(
            """
            INSERT INTO job_user (job_id, user_id)
            VALUES (?, ?)
            """, (
                job_id,
                user_id,
            ))
    except OperationalError as err:
        log.exception('Failed %s', err)
        raise DatabaseError(err)


def is_job_user(conn: Connection, job_id: str, user_id: str) -> bool:
    log = getLogger(__name__ + ':is_job_user')
    try:
        log.debug('<job:%s>, <user:%s>', job_id, user_id)
        cursor = conn.execute(
            """
            SELECT 1
              FROM job_user
             WHERE job_id = ?
                   AND user_id = ?
            """, (
                job_id,
                user_id,
            ))
        return cursor.rowcount == 1
    except OperationalError as err:
        log.exception('Failed %s', err)
        raise DatabaseError(err)


def select_job(conn: Connection, job_id: str) -> Cursor:
    log = getLogger(__name__ + ':select_job')
    try:
        log.debug('<%s>', job_id)
        cursor = conn.execute(
            """
            SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.detections_id,
                   j.name, j.scene_id, j.status,
                   e.error_message, e.execution_step,
                   s.geometry, s.sensor_name AS scene_sensor_name, s.captured_on AS scene_capture_date
              FROM job j
                   LEFT OUTER JOIN job_error e ON (e.job_id = j.job_id)
                   LEFT OUTER JOIN scene s ON (s.scene_id = j.scene_id)
             WHERE j.job_id = ?
            """, (
                job_id,
            ))
        return cursor
    except OperationalError as err:
        log.exception('Failed %s', err)
        raise DatabaseError(err)


def select_jobs_for_user(conn: Connection, user_id: str):
    log = getLogger(__name__ + ':select_jobs_for_user')
    try:
        log.debug('<%s>', user_id)
        cursor = conn.execute(
            """
            SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.detections_id,
                   j.name, j.scene_id, j.status,
                   e.error_message, e.execution_step,
                   s.geometry, s.sensor_name AS scene_sensor_name, s.captured_on AS scene_capture_date
              FROM job j
                   LEFT OUTER JOIN job_user u ON (u.job_id = j.job_id)
                   LEFT OUTER JOIN job_error e ON (e.job_id = j.job_id)
                   LEFT OUTER JOIN scene s ON (s.scene_id = j.scene_id)
             WHERE u.user_id = ?
            """, (
                user_id,
            ))
        return cursor
    except OperationalError as err:
        log.exception('Failed %s', err)
        raise DatabaseError(err)
