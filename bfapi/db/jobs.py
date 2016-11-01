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

import psycopg2 as pg

from bfapi.db import Connection, Cursor, DatabaseError


def delete_job_user(
        conn: Connection,
        *,
        job_id: str,
        user_id: str) -> bool:
    query = """
        DELETE FROM __beachfront__job_user
        WHERE job_id = %(job_id)s
              AND user_id = %(user_id)s
        """
    params = {
        'job_id': job_id,
        'user_id': user_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount > 0
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def exists(
        conn: Connection,
        *,
        job_id: str) -> bool:
    query = """
        SELECT 1 FROM __beachfront__job WHERE job_id = %(job_id)s
        """
    params = {
        'job_id': job_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return len(cursor.fetchall()) > 0
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def insert_detection(
        conn: Connection,
        *,
        job_id: str,
        feature_collection: str):
    # FIXME -- I know we can do better than this...
    query = """
    INSERT INTO __beachfront__detection (job_id, feature_id, geometry)
    SELECT %(job_id)s AS job_id,
           row_number() OVER () AS feature_id,
           ST_GeomFromGeoJSON(fc.features->>'geometry') AS geometry
    FROM (SELECT json_array_elements(%(feature_collection)s::json->'features') AS features) fc
    """
    params = {
        'job_id': job_id,
        'feature_collection': feature_collection,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def insert_job(
        conn: Connection,
        *,
        algorithm_id: str,
        algorithm_name: str,
        algorithm_version: int,
        job_id: str,
        name: str,
        scene_id: str,
        status: str,
        user_id: str):
    query = """
        INSERT INTO __beachfront__job (job_id, algorithm_id, algorithm_name, algorithm_version, created_by, name, scene_id, status)
        VALUES (%(job_id)s, %(algorithm_id)s, %(algorithm_name)s, %(algorithm_version)s, %(created_by)s, %(name)s, %(scene_id)s, %(status)s)
        """
    params = {
        'job_id': job_id,
        'algorithm_id': algorithm_id,
        'algorithm_name': algorithm_name,
        'algorithm_version': algorithm_version,
        'created_by': user_id,
        'name': name,
        'scene_id': scene_id,
        'status': status,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def insert_job_failure(
        conn: Connection,
        *,
        error_message: str,
        execution_step: str,
        job_id: str) -> None:
    query = """
        INSERT INTO __beachfront__job_error (job_id, error_message, execution_step)
        VALUES (%(job_id)s, %(error_message)s, %(execution_step)s)
        """
    params = {
        'job_id': job_id,
        'error_message': error_message or None,
        'execution_step': execution_step,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def insert_job_user(
        conn: Connection,
        *,
        job_id: str,
        user_id: str) -> None:
    query = """
        INSERT INTO __beachfront__job_user (job_id, user_id)
        VALUES (%(job_id)s, %(user_id)s)
        ON CONFLICT DO NOTHING
        """
    params = {
        'job_id': job_id,
        'user_id': user_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def select_job(
        conn: Connection,
        *,
        job_id: str) -> Cursor:
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.detections_id,
               j.name, j.scene_id, j.status,
               e.error_message, e.execution_step,
               ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name AS scene_sensor_name, s.captured_on AS scene_capture_date
          FROM __beachfront__job j
               LEFT OUTER JOIN __beachfront__job_error e ON (e.job_id = j.job_id)
               LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
         WHERE j.job_id = %(job_id)s
        """
    params = {
        'job_id': job_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def select_jobs_for_inputs(
        conn: Connection,
        *,
        algorithm_id: str,
        scene_id: str) -> Cursor:
    query = """
        SELECT job_id
          FROM __beachfront__job
         WHERE algorithm_id = %(algorithm_id)s
           AND scene_id = %(scene_id)s
           AND status IN ('Running', 'Success')
         ORDER BY status DESC  -- Success first
        """
    params = {
        'algorithm_id': algorithm_id,
        'scene_id': scene_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def select_jobs_for_productline(
        conn: Connection,
        *,
        productline_id: str) -> Cursor:
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.detections_id,
               j.name, j.scene_id, j.status,
               ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name AS scene_sensor_name, s.captured_on AS scene_capture_date
          FROM __beachfront__productline_job p
               LEFT OUTER JOIN __beachfront__job j ON (j.job_id = p.job_id)
               LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
         WHERE p.productline_id = %(productline_id)s
        ORDER BY created_on ASC
        """
    params = {
        'productline_id': productline_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def select_jobs_for_scene(
        conn: Connection,
        *,
        scene_id: str) -> Cursor:
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.detections_id,
               j.name, j.scene_id, j.status,
               ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name AS scene_sensor_name, s.captured_on AS scene_capture_date
          FROM __beachfront__job j
               LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
         WHERE j.scene_id = %(scene_id)s
           AND j.status IN ('Success', 'Running')
        ORDER BY created_on ASC
        """
    params = {
        'scene_id': scene_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def select_jobs_for_user(
        conn: Connection,
        *,
        user_id: str) -> Cursor:
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.detections_id,
               j.name, j.scene_id, j.status,
               e.error_message, e.execution_step,
               ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name AS scene_sensor_name, s.captured_on AS scene_capture_date
          FROM __beachfront__job j
               LEFT OUTER JOIN __beachfront__job_user u ON (u.job_id = j.job_id)
               LEFT OUTER JOIN __beachfront__job_error e ON (e.job_id = j.job_id)
               LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
         WHERE u.user_id = %(user_id)s
        ORDER BY created_on ASC
        """
    params = {
        'user_id': user_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def select_summary_for_status(
        conn: Connection,
        *,
        status: str) -> Cursor:
    query = """
        SELECT job_id, created_on
          FROM __beachfront__job
         WHERE status = %(status)s
        """
    params = {
        'status': status,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def update_status(
        conn: Connection,
        *,
        data_id: str,
        job_id: str,
        status: str) -> Cursor:
    query = """
        UPDATE __beachfront__job
           SET detections_id = %(detections_id)s,
               status = %(status)s
         WHERE job_id = %(job_id)s
        """
    params = {
        'job_id': job_id,
        'status': status,
        'detections_id': data_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
    except pg.Error as err:
        raise DatabaseError(err, query, params)
