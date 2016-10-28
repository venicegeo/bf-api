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

import logging
import re
from datetime import datetime

import dateutil.parser
import requests

from bfapi import piazza
from bfapi.config import CATALOG, PZ_GATEWAY, SYSTEM_API_KEY
from bfapi.db import get_connection, scenes, DatabaseError

PATTERN_VALID_EVENT_TYPE_ID = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')


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

def get(scene_id: str) -> Scene:
    log = logging.getLogger(__name__)

    if not re.match(r'^landsat:\w+$', scene_id):
        raise MalformedSceneID(scene_id)

    scene_uri = 'https://{}/image/{}'.format(CATALOG, scene_id)
    try:
        log.info('Fetch `%s`', scene_uri)
        scene_req = requests.get(scene_uri)
        scene_req.raise_for_status()
    except requests.ConnectionError:
        raise CatalogError()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 404:
            raise NotFound(scene_id)
        # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
        # TODO -- this can go away once Redmine #9287 is closed
        if status_code == 400 and '{}: redis: nil even using wildcard search'.format(scene_id) in err.response.text:
            raise NotFound(scene_id)
        # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
        raise CatalogError()

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


def get_event_type_id() -> str:
    log = logging.getLogger(__name__)
    log.info("Requesting Image Catalog's event type ID")

    try:
        response = requests.get(
            'https://{}/eventTypeID'.format(CATALOG),
            params={
                'pzGateway': 'https://{}'.format(PZ_GATEWAY),
            },
            headers={
                'Authorization': piazza.to_auth_header(SYSTEM_API_KEY),
            }
        )
        response.raise_for_status()
    except (requests.ConnectionError, requests.HTTPError):
        raise CatalogError()

    event_type_id = response.text.strip()
    if not PATTERN_VALID_EVENT_TYPE_ID.match(event_type_id):
        log.error('Received invalid event type ID `%s`', event_type_id)
        raise CatalogError()

    return event_type_id


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

class CatalogError(Exception):
    def __init__(self):
        super().__init__('error communicating with image catalog')


class MalformedSceneID(Exception):
    def __init__(self, scene_id: str):
        super().__init__('malformed scene id `{}`'.format(scene_id))
        self.scene_id = scene_id


class NotFound(Exception):
    def __init__(self, scene_id: str):
        super().__init__('scene `{}` not found in catalog'.format(scene_id))
        self.scene_id = scene_id


class ValidationError(Exception):
    def __init__(self, scene_id: str, message: str):
        super().__init__('scene `{}` has invalid metadata: {}'.format(scene_id, message))
        self.scene_id = scene_id
