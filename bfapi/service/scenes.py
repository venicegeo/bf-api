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
import re
from logging import getLogger

import dateutil.parser
import requests

from bfapi.config import CATALOG
from bfapi.db import get_connection, scenes, DatabaseError


#
# Types
#

class Scene:
    def __init__(
            self,
            bands: dict,
            capture_date: datetime,
            cloud_cover: float,
            geometry: dict,
            resolution: int,
            scene_id: str,
            sensor_name: str,
            uri: str):
        self.bands = bands
        self.capture_date = capture_date
        self.cloud_cover = cloud_cover
        self.id = scene_id
        self.geometry = geometry
        self.resolution = resolution
        self.sensor_name = sensor_name
        self.uri = uri


#
# Actions
#

def fetch(scene_id: str) -> Scene:
    log = getLogger(__name__ + ':fetch')

    if not re.match(r'^landsat:\w+$', scene_id):
        raise InvalidIDError(scene_id)

    scene_uri = 'https://{}/image/{}'.format(CATALOG, scene_id)
    try:
        log.info('fetch `%s`', scene_uri)
        scene_req = requests.get(scene_uri)
        scene_req.raise_for_status()
    except (requests.ConnectionError, requests.HTTPError) as err:
        log.error('Could not fetch scene metadata: %s', err)
        raise FetchError(scene_id)

    geojson = scene_req.json()
    scene = Scene(
        scene_id=scene_id,
        uri=scene_uri,
        capture_date=_extract_capture_date(scene_id, geojson),
        bands=_extract_bands(scene_id, geojson),
        cloud_cover=_extract_cloud_cover(scene_id, geojson),
        geometry=_extract_geometry(scene_id, geojson),
        resolution=_extract_resolution(scene_id, geojson),
        sensor_name=_extract_sensor_name(scene_id, geojson),
    )

    conn = get_connection()
    try:
        scenes.insert(
            conn,
            scene_id=scene.id,
            captured_on=scene.capture_date,
            catalog_uri=scene.uri,
            cloud_cover=scene.cloud_cover,
            geometry=scene.geometry,
            resolution=scene.resolution,
            sensor_name=scene.sensor_name,
        )
        conn.commit()
    except DatabaseError as err:
        conn.rollback()
        log.error('Could not save scene to database: %s', err)
        err.print_diagnostics()
        raise err

    return scene


#
# Helpers
#

def _extract_capture_date(scene_id: str, feature: dict) -> datetime:
    value = feature['properties'].get('acquiredDate')
    if value is None:
        raise ValidationError(scene_id, 'missing `acquiredDate`')
    try:
        value = dateutil.parser.parse(value)
    except Exception as err:
        raise ValidationError(scene_id, 'could not parse `acquiredDate`: ({})'.format(err))
    return value


def _extract_bands(scene_id: str, feature: dict) -> dict:
    value = feature['properties'].get('bands')
    if value is None:
        raise ValidationError(scene_id, 'missing `bands`')
    if not isinstance(value, dict):
        raise ValidationError(scene_id, '`bands` is not a dictionary')
    return value


def _extract_cloud_cover(scene_id: str, feature: dict) -> float:
    value = feature['properties'].get('cloudCover')
    if value is None:
        raise ValidationError(scene_id, 'missing `cloudCover`')
    try:
        value = float(value)
    except:
        raise ValidationError(scene_id, '`cloudCover` is not a float')
    return value


def _extract_geometry(scene_id: str, feature: dict) -> dict:
    value = feature.get('geometry')
    if value is None:
        raise ValidationError(scene_id, 'missing `geometry`')
    if not isinstance(value, dict):
        raise ValidationError(scene_id, '`geometry` is not a dictionary')
    return value


def _extract_resolution(scene_id: str, feature: dict) -> int:
    value = feature['properties'].get('resolution')
    if value is None:
        raise ValidationError(scene_id, 'missing `resolution`')
    try:
        return int(value)
    except:
        raise ValidationError(scene_id, '`resolution` is not an int')


def _extract_sensor_name(scene_id: str, feature: dict) -> str:
    value = feature['properties'].get('sensorName')
    if value is None:
        raise ValidationError(scene_id, 'missing `sensorName`')
    return value.strip()


#
# Errors
#

class InvalidIDError(Exception):
    def __init__(self, scene_id: str):
        super().__init__('InvalidIDError (scene_id={})'.format(scene_id))
        self.scene_id = scene_id


class FetchError(Exception):
    def __init__(self, scene_id: str):
        super().__init__('FetchError (scene_id={})'.format(scene_id))
        self.scene_id = scene_id


class ValidationError(Exception):
    def __init__(self, scene_id: str, message: str):
        super().__init__('ValidationError (scene_id={}): {}'.format(scene_id, message))
        self.scene_id = scene_id
        self.message = message
