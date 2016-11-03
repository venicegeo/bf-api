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

import sqlalchemy.exc as sae

from bfapi.db import Connection, DatabaseError


def insert(conn: Connection,
           *,
           captured_on: datetime,
           catalog_uri: str,
           cloud_cover: float,
           geometry: dict,
           resolution: int,
           scene_id: str,
           sensor_name: str) -> str:
    query = """
        INSERT INTO __beachfront__scene (scene_id, captured_on, catalog_uri, cloud_cover, geometry, resolution, sensor_name)
        VALUES (%(scene_id)s, %(captured_on)s, %(catalog_uri)s, %(cloud_cover)s, ST_GeomFromGeoJSON(%(geometry)s),
               %(resolution)s, %(sensor_name)s)
        ON CONFLICT DO NOTHING
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
        return conn.execute(query, params)
    except sae.DatabaseError as err:
        raise DatabaseError(err)
