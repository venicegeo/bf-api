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


def select_all(conn: Connection):
    query = """
        SELECT productline_id, algorithm_id, algorithm_name, category, compute_mask, created_by,
               created_on, max_cloud_cover, name, owned_by, spatial_filter_id, start_on, stop_on,
               ST_AsGeoJSON(bbox) AS bbox
          FROM __beachfront__productline
         ORDER BY created_on ASC
        """
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor
    except pg.Error as err:
        raise DatabaseError(err, query)


def select_summary_for_scene(
        conn: Connection,
        *,
        cloud_cover: int,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float) -> Cursor:
    query = """
        SELECT productline_id, algorithm_id, name, owned_by
          FROM __beachfront__productline
         WHERE bbox && ST_MakeEnvelope(%(min_x)s, %(min_y)s, %(max_x)s, %(max_y)s)
           AND max_cloud_cover >= %(cloud_cover)s
           AND start_on <= CURRENT_DATE
           AND (stop_on >= CURRENT_DATE OR stop_on IS NULL)
        """
    params = {
        'cloud_cover': cloud_cover,
        'min_x': min_x,
        'min_y': min_y,
        'max_x': max_x,
        'max_y': max_y,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    except pg.Error as err:
        raise DatabaseError(err, query, params)


def insert_productline_job(
        conn: Connection,
        *,
        job_id: str,
        productline_id: str):
    query = """
        INSERT INTO __beachfront__productline_job (job_id, productline_id)
        VALUES (%(job_id)s, %(productline_id)s)
        ON CONFLICT DO NOTHING
        """
    params = {
        'job_id': job_id,
        'productline_id': productline_id,
    }
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    except pg.Error as err:
        raise DatabaseError(err, query, params)
