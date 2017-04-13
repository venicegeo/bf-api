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

from datetime import datetime
import logging
from bfapi.db import Connection, ResultProxy

def delete_job_user(
        conn: Connection,
        *,
        job_id: str,
        user_id: str) -> bool:
    log = logging.getLogger(__name__)
    log.info('Db delete job user', action='database delete record')
    query = """
        DELETE FROM __beachfront__job_user
        WHERE job_id = %(job_id)s
              AND user_id = %(user_id)s
        """
    params = {
        'job_id': job_id,
        'user_id': user_id,
    }
    return conn.execute(query, params).rowcount > 0


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
    return conn.execute(query, params).rowcount > 0


def insert_detection(
        conn: Connection,
        *,
        job_id: str,
        feature_collection: str) -> None:
    # FIXME -- I know we can do better than this...
    log = logging.getLogger(__name__)
    log.info('Db insert detection', action='database insert record')
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
    conn.execute(query, params)


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
        tide: float,
        tide_min_24h: float,
        tide_max_24h: float,
        user_id: str) -> None:

    log = logging.getLogger(__name__)
    log.info('Db insert job', action='database insert record')
    query = """
        INSERT INTO __beachfront__job (job_id, algorithm_id, algorithm_name, algorithm_version, created_by, name,
                                       scene_id, status, tide, tide_min_24h, tide_max_24h)
        VALUES (%(job_id)s, %(algorithm_id)s, %(algorithm_name)s, %(algorithm_version)s, %(created_by)s, %(name)s,
                %(scene_id)s, %(status)s, %(tide)s, %(tide_min_24h)s, %(tide_max_24h)s)
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
        'tide': tide,
        'tide_min_24h': tide_min_24h,
        'tide_max_24h': tide_max_24h,
    }
    conn.execute(query, params)


def insert_job_failure(
        conn: Connection,
        *,
        error_message: str,
        execution_step: str,
        job_id: str) -> None:
    log = logging.getLogger(__name__)
    log.info('Db insert job failure', action='database insert record')
    query = """
        INSERT INTO __beachfront__job_error (job_id, error_message, execution_step)
        VALUES (%(job_id)s, %(error_message)s, %(execution_step)s)
        """
    params = {
        'job_id': job_id,
        'error_message': error_message or None,
        'execution_step': execution_step,
    }
    conn.execute(query, params)


def insert_job_user(
        conn: Connection,
        *,
        job_id: str,
        user_id: str) -> None:
    log = logging.getLogger(__name__)
    log.info('Db job user', action='database insert record')
    query = """
        INSERT INTO __beachfront__job_user (job_id, user_id)
        VALUES (%(job_id)s, %(user_id)s)
        ON CONFLICT DO NOTHING
        """
    params = {
        'job_id': job_id,
        'user_id': user_id,
    }
    conn.execute(query, params)


def select_detections(
        conn: Connection,
        *,
        job_id: str) -> ResultProxy:
    # Construct the GeoJSON directly where the data lives
    log = logging.getLogger(__name__)
    log.info('Db select detection', action='database query record')
    query = """
        SELECT to_json(fc)::text AS "feature_collection"
          FROM (SELECT 'FeatureCollection' AS "type",
                       array_agg(f) AS "features"
                  FROM (SELECT concat_ws('#', d.job_id, d.feature_id) AS "id",
                               to_json(p) AS "properties",
                               ST_AsGeoJSON(d.geometry)::json AS "geometry",
                               'Feature' AS "type"
                          FROM __beachfront__detection d
                               INNER JOIN __beachfront__provenance AS p ON (p.job_id = d.job_id)
                         WHERE d.job_id = %(job_id)s
                       ) AS f
               ) AS fc
        """
    params = {
        'job_id': job_id,
    }
    return conn.execute(query, params)


def select_job(
        conn: Connection,
        *,
        job_id: str) -> ResultProxy:
    log = logging.getLogger(__name__)
    log.info('Db select job', action='database query record')
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.name, j.scene_id, j.status, j.tide, j.tide_min_24h, j.tide_max_24h,
               e.error_message, e.execution_step,
               ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name, s.captured_on
          FROM __beachfront__job j
               LEFT OUTER JOIN __beachfront__job_error e ON (e.job_id = j.job_id)
               LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
         WHERE j.job_id = %(job_id)s
        """
    params = {
        'job_id': job_id,
    }
    return conn.execute(query, params)


def select_jobs_for_inputs(
        conn: Connection,
        *,
        algorithm_id: str,
        scene_id: str) -> ResultProxy:
    log = logging.getLogger(__name__)
    log.info('Db select jobs for inputs', action='database query record')
    query = """
        SELECT job_id,
               CASE status
                    WHEN 'Success' THEN 0
                    WHEN 'Submitted' THEN 1
                    WHEN 'Running' THEN 2
               END AS _sort_precedence
          FROM __beachfront__job
         WHERE algorithm_id = %(algorithm_id)s
           AND scene_id = %(scene_id)s
           AND status IN ('Submitted', 'Running', 'Success')
         ORDER BY _sort_precedence ASC
        """
    params = {
        'algorithm_id': algorithm_id,
        'scene_id': scene_id,
    }
    return conn.execute(query, params)


def select_jobs_for_productline(
        conn: Connection,
        *,
        productline_id: str,
        since: datetime) -> ResultProxy:
    log = logging.getLogger(__name__)
    log.info('Db select jobs for productline', action='database query record')
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.name, j.scene_id, j.status, j.tide, j.tide_min_24h, j.tide_max_24h,
               ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name, s.captured_on
          FROM __beachfront__productline_job p
               LEFT OUTER JOIN __beachfront__job j ON (j.job_id = p.job_id)
               LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
         WHERE p.productline_id = %(productline_id)s
           AND (j.status IN ('Submitted', 'Running', 'Success'))
           AND (s.captured_on >= %(since)s)
        ORDER BY captured_on DESC
        """
    params = {
        'productline_id': productline_id,
        'since': since,
    }
    return conn.execute(query, params)


def select_jobs_for_scene(
        conn: Connection,
        *,
        scene_id: str) -> ResultProxy:
    log = logging.getLogger(__name__)
    log.info('Db select jobs for scene', action='database select record')
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.name, j.scene_id, j.status, j.tide, j.tide_min_24h, j.tide_max_24h,
               ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name, s.captured_on
          FROM __beachfront__job j
               LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
         WHERE j.scene_id = %(scene_id)s
           AND j.status IN ('Submitted', 'Running', 'Success')
        ORDER BY created_on DESC
        """
    params = {
        'scene_id': scene_id,
    }
    return conn.execute(query, params)


def select_for_existing_jobs(
        conn: Connection,
        *,
        algorithm_id: str,
        scene_id: str) -> ResultProxy:
    log = logging.getLogger(__name__)
    log.info('Db select jobs for scene and algorithm', action='database select record')
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.name, j.scene_id, j.status, j.tide, j.tide_min_24h, j.tide_max_24h,
               ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name, s.captured_on
          FROM __beachfront__job j
               LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
         WHERE j.scene_id = %(scene_id)s
           AND algorithm_id = %(algorithm_id)s
           AND j.status IN ('Submitted', 'Running', 'Success')
        ORDER BY created_on DESC
        """
    params = {
        'algorithm_id': algorithm_id,
        'scene_id': scene_id,
    }
    return conn.execute(query, params)


def select_jobs_for_user(
        conn: Connection,
        *,
        user_id: str) -> ResultProxy:
    log = logging.getLogger(__name__)
    log.info('Db select jobs for users', action='database query record')
    query = """
        SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.name, j.scene_id, j.status, j.tide, j.tide_min_24h, j.tide_max_24h,
               e.error_message, e.execution_step,
               ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name, s.captured_on
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
    return conn.execute(query, params)


def select_outstanding_jobs(conn: Connection) -> ResultProxy:
    log = logging.getLogger(__name__)
    log.info('Db select outstanding jobs', action='database query record')
    query = """
        SELECT job_id,
               DATE_TRUNC('second', NOW() - created_on) AS age
          FROM __beachfront__job
         WHERE status IN ('Submitted', 'Pending', 'Running')
        ORDER BY created_on ASC
        """
    return conn.execute(query)


def update_status(
        conn: Connection,
        *,
        job_id: str,
        status: str) -> None:
    log = logging.getLogger(__name__)
    log.info('Db update status', action='database update record')
    query = """
        UPDATE __beachfront__job
           SET status = %(status)s
         WHERE job_id = %(job_id)s
        """
    params = {
        'job_id': job_id,
        'status': status,
    }
    conn.execute(query, params)
