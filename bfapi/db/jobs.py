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

from sqlite3 import Connection, Cursor, IntegrityError, OperationalError

from bfapi.db import DatabaseError


def delete_job_user(
        conn: Connection,
        job_id: str,
        user_id: str) -> bool:
    query = """
        DELETE FROM job_user
        WHERE job_id = :job_id
              AND user_id = :user_id
        """
    params = {
        'job_id': job_id,
        'user_id': user_id,
    }
    try:
        cursor = conn.execute(query, params)
        return cursor.rowcount > 0
    except OperationalError as err:
        raise DatabaseError(err, query, params)


def exists(
        conn: Connection,
        job_id: str) -> bool:
    query = """
        SELECT 1 FROM job WHERE job_id = :job_id
        """
    params = {
        'job_id': job_id,
    }
    try:
        cursor = conn.execute(query, params)
        return len(cursor.fetchall()) > 0
    except OperationalError as err:
        raise DatabaseError(err, query, params)


def insert_job(
        conn: Connection,
        algorithm_name: str,
        algorithm_version: int,
        job_id: str,
        name: str,
        scene_id: str,
        status: str,
        user_id: str):
    query = """
        INSERT INTO job (job_id, algorithm_name, algorithm_version, created_by, name, scene_id, status)
        VALUES (:job_id, :algorithm_name, :algorithm_version, :created_by, :name, :scene_id, :status)
        """
    params = {
        'job_id': job_id,
        'algorithm_name': algorithm_name,
        'algorithm_version': algorithm_version,
        'created_by': user_id,
        'name': name,
        'scene_id': scene_id,
        'status': status,
    }
    try:
        conn.execute(query, params)
    except (IntegrityError, OperationalError) as err:
        raise DatabaseError(err, query, params)


def insert_job_failure(
        conn: Connection,
        error_message: str,
        execution_step: str,
        job_id: str) -> None:
    query = """
        INSERT INTO job_error (job_id, error_message, execution_step)
        VALUES (:job_id, :error_message, :execution_step)
        """
    params = {
        'job_id': job_id,
        'error_message': error_message or None,
        'execution_step': execution_step,
    }
    try:
        conn.execute(query, params)
    except (IntegrityError, OperationalError) as err:
        raise DatabaseError(err, query, params)


def insert_job_user(
        conn: Connection,
        job_id: str,
        user_id: str) -> None:
    query = """
        INSERT OR IGNORE INTO job_user (job_id, user_id)
        VALUES (:job_id, :user_id)
        """
    params = {
        'job_id': job_id,
        'user_id': user_id,
    }
    try:
        conn.execute(query, params)
    except (IntegrityError, OperationalError) as err:
        raise DatabaseError(err, query, params)


def select_job(
        conn: Connection,
        job_id: str) -> Cursor:
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.detections_id,
               j.name, j.scene_id, j.status,
               e.error_message, e.execution_step,
               s.geometry, s.sensor_name AS scene_sensor_name, s.captured_on AS scene_capture_date
          FROM job j
               LEFT OUTER JOIN job_error e ON (e.job_id = j.job_id)
               LEFT OUTER JOIN scene s ON (s.scene_id = j.scene_id)
         WHERE j.job_id = :job_id
        """
    params = {
        'job_id': job_id,
    }
    try:
        cursor = conn.execute(query, params)
        return cursor
    except OperationalError as err:
        raise DatabaseError(err, query, params)


def select_jobs_for_user(
        conn: Connection,
        user_id: str):
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.detections_id,
               j.name, j.scene_id, j.status,
               e.error_message, e.execution_step,
               s.geometry, s.sensor_name AS scene_sensor_name, s.captured_on AS scene_capture_date
          FROM job j
               LEFT OUTER JOIN job_user u ON (u.job_id = j.job_id)
               LEFT OUTER JOIN job_error e ON (e.job_id = j.job_id)
               LEFT OUTER JOIN scene s ON (s.scene_id = j.scene_id)
         WHERE u.user_id = :user_id
        """
    params = {
        'user_id': user_id,
    }
    try:
        cursor = conn.execute(query, params)
        return cursor
    except OperationalError as err:
        raise DatabaseError(err, query, params)


def select_summary_for_status(
        conn: Connection,
        status: str) -> Cursor:
    query = """
        SELECT job_id, created_on
          FROM job
         WHERE status = :status
        """
    params = {
        'status': status,
    }
    try:
        cursor = conn.execute(query, params)
        return cursor
    except OperationalError as err:
        raise DatabaseError(err, query, params)


def update_status(
        conn: Connection,
        data_id: str,
        job_id: str,
        status: str) -> Cursor:
    query = """
        UPDATE job
           SET detections_id = :detections_id,
               status = :status
         WHERE job_id = :job_id
        """
    params = {
        'job_id': job_id,
        'status': status,
        'detections_id': data_id,
    }
    try:
        conn.execute(query, params)
    except (IntegrityError, OperationalError) as err:
        raise DatabaseError(err, query, params)
