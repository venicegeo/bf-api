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

from datetime import date

from bfapi.db import Connection, ResultProxy


def delete_productline(
        conn: Connection,
        *,
        productline_id: str) -> ResultProxy:
    query = """
        UPDATE __beachfront__productline
           SET deleted = TRUE
         WHERE productline_id = %(productline_id)s
    """
    params = {
        'productline_id': productline_id,
    }
    return conn.execute(query, params)


def insert_productline(
        conn: Connection,
        *,
        productline_id: str,
        algorithm_id: str,
        algorithm_name: str,
        bbox: tuple,
        category: str = None,
        max_cloud_cover: int,
        name: str,
        spatial_filter_id: str = None,
        start_on: date,
        stop_on: date = None,
        user_id: str) -> ResultProxy:
    query = """
        INSERT INTO __beachfront__productline (productline_id, algorithm_id, algorithm_name, category, created_by, max_cloud_cover, name, owned_by, spatial_filter_id, start_on, stop_on, bbox)
        VALUES (%(productline_id)s, %(algorithm_id)s, %(algorithm_name)s, %(category)s, %(user_id)s, %(max_cloud_cover)s, %(name)s, %(user_id)s, %(spatial_filter_id)s, %(start_on)s, %(stop_on)s, ST_MakeEnvelope(%(min_x)s, %(min_y)s, %(max_x)s, %(max_y)s))
        """
    params = {
        'productline_id': productline_id,
        'algorithm_id': algorithm_id,
        'algorithm_name': algorithm_name,
        'category': category,
        'compute_mask': None,
        'max_cloud_cover': max_cloud_cover,
        'min_x': bbox[0],
        'min_y': bbox[1],
        'max_x': bbox[2],
        'max_y': bbox[3],
        'name': name,
        'spatial_filter_id': spatial_filter_id,
        'start_on': start_on,
        'stop_on': stop_on,
        'user_id': user_id,
    }
    return conn.execute(query, params)


def insert_productline_job(
        conn: Connection,
        *,
        job_id: str,
        productline_id: str) -> ResultProxy:
    query = """
        INSERT INTO __beachfront__productline_job (job_id, productline_id)
        VALUES (%(job_id)s, %(productline_id)s)
        ON CONFLICT DO NOTHING
        """
    params = {
        'job_id': job_id,
        'productline_id': productline_id,
    }
    return conn.execute(query, params)


def select_all(conn: Connection):
    query = """
        SELECT productline_id, algorithm_id, algorithm_name, category, compute_mask, created_by,
               created_on, max_cloud_cover, name, owned_by, spatial_filter_id, start_on, stop_on,
               ST_AsGeoJSON(bbox) AS bbox
          FROM __beachfront__productline
         WHERE NOT deleted
         ORDER BY created_on ASC
        """
    return conn.execute(query)


def select_productline(
        conn: Connection,
        *,
        productline_id: str) -> ResultProxy:
    query = """
        SELECT productline_id, algorithm_id, algorithm_name, category, compute_mask, created_by,
               created_on, max_cloud_cover, name, owned_by, spatial_filter_id, start_on, stop_on,
               ST_AsGeoJSON(bbox) AS bbox
          FROM __beachfront__productline
         WHERE NOT deleted
           AND productline_id = %(productline_id)s
    """
    params = {
        'productline_id': productline_id,
    }
    return conn.execute(query, params)


def select_summary_for_scene(
        conn: Connection,
        *,
        captured_on: date,
        cloud_cover: int,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float) -> ResultProxy:
    query = """
        SELECT productline_id, algorithm_id, name, owned_by
          FROM __beachfront__productline
         WHERE NOT deleted
           AND bbox && ST_MakeEnvelope(%(min_x)s, %(min_y)s, %(max_x)s, %(max_y)s)
           AND max_cloud_cover >= %(cloud_cover)s
           AND start_on <= %(captured_on)s
           AND (stop_on >= %(captured_on)s OR stop_on IS NULL)
        """
    params = {
        'captured_on': captured_on,
        'cloud_cover': cloud_cover,
        'min_x': min_x,
        'min_y': min_y,
        'max_x': max_x,
        'max_y': max_y,
    }
    return conn.execute(query, params)
