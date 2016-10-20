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
from datetime import datetime
from sqlite3 import Connection, IntegrityError, OperationalError

from bfapi.db import DatabaseError


def insert(conn: Connection,
           scene_id: str,
           captured_on: datetime,
           catalog_uri: str,
           cloud_cover: float,
           geometry: dict,
           resolution: int,
           sensor_name: str) -> str:
    query = """
        INSERT OR IGNORE INTO __beachfront__scene (scene_id, captured_on, catalog_uri, cloud_cover, geometry, resolution, sensor_name)
        VALUES (:scene_id, :captured_on, :catalog_uri, :cloud_cover, :geometry, :resolution, :sensor_name)
        """
    params = {
        'scene_id': scene_id,
        'captured_on': captured_on,
        'catalog_uri': catalog_uri,
        'cloud_cover': cloud_cover,
        'geometry': json.dumps(geometry),
        'resolution': resolution,
        'sensor_name': sensor_name,
    }
    try:
        conn.execute(query, params)
    except (IntegrityError, OperationalError) as err:
        raise DatabaseError(err, query, params)
