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

from bfapi import db
from bfapi.config import CATALOG, PLANET


PATTERN_LANDSAT = re.compile(r'^landsat:\w+$')
PATTERN_PLANET = re.compile(r'^(planetscope|rapideye):[\w_-]+$')

#
# Types
#

class Scene:
    def __init__(
            self,
            *,
            capture_date: datetime,
            cloud_cover: float,
            geotiff_coastal: str = None,
            geotiff_multispectral: str = None,
            geotiff_swir1: str = None,
            geometry: dict,
            is_active: bool,
            resolution: int,
            scene_id: str,
            sensor_name: str,
            uri: str):
        self.capture_date = capture_date
        self.cloud_cover = cloud_cover
        self.id = scene_id
        self.geometry = geometry
        self.geotiff_coastal = geotiff_coastal
        self.geotiff_multispectral = geotiff_multispectral
        self.geotiff_swir1 = geotiff_swir1
        self.is_active = is_active
        self.resolution = resolution
        self.sensor_name = sensor_name
        self.uri = uri


#
# Actions
#

def get(scene_id: str, planet_api_key: str = None) -> Scene:
    log = logging.getLogger(__name__)

    if PATTERN_LANDSAT.match(scene_id):
        return _get_from_legacy_catalog(scene_id)
    if not PATTERN_PLANET.match(scene_id):
        raise MalformedSceneID(scene_id)

    platform, external_id = scene_id.split(':', 1)

    uri = 'https://{}/planet/{}/{}'.format(PLANET, platform, external_id)
    log.info('Fetch `%s`', uri)
    try:
        log.debug('Requesting metadata; url=`%s`', uri)
        response = requests.get(
            uri,
            params={
                'PL_API_KEY': planet_api_key,
            }
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise CatalogError()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 404:
            raise NotFound(scene_id)
        raise CatalogError()

    feature = response.json()

    geotiff_multispectral = feature['properties'].get('location')
    scene = Scene(
        scene_id=scene_id,
        uri=uri,
        capture_date=_extract_capture_date(scene_id, feature),
        cloud_cover=_extract_cloud_cover(scene_id, feature),
        geometry=_extract_geometry(scene_id, feature),
        geotiff_multispectral=geotiff_multispectral,
        is_active=_extract_activation_status(scene_id, feature),
        resolution=_extract_resolution(scene_id, feature),
        sensor_name=_extract_sensor_name(scene_id, feature),
    )

    _save_to_database(scene)
    return scene


#
# Helpers
#

def _get_from_legacy_catalog(scene_id: str) -> Scene:
    log = logging.getLogger(__name__)
    scene_uri = 'https://{}/image/{}'.format(CATALOG, scene_id)
    try:
        log.info('Fetch `%s`', scene_uri)
        response = requests.get(scene_uri)
        response.raise_for_status()
    except requests.ConnectionError:
        raise CatalogError()
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 404:
            raise NotFound(scene_id)
        raise CatalogError()

    feature = response.json()
    geotiff_coastal, geotiff_swir1 = _extract_bands(scene_id, feature)
    scene = Scene(
        scene_id=scene_id,
        uri=scene_uri,
        capture_date=_extract_capture_date(scene_id, feature),
        cloud_cover=_extract_cloud_cover(scene_id, feature),
        geometry=_extract_geometry(scene_id, feature),
        geotiff_coastal=geotiff_coastal,
        geotiff_swir1=geotiff_swir1,
        is_active=True,
        resolution=_extract_resolution(scene_id, feature),
        sensor_name=_extract_sensor_name(scene_id, feature),
    )

    _save_to_database(scene)
    return scene


def _extract_activation_status(scene_id: str, feature) -> bool:
    value = feature['properties'].get('status')
    if value is None:
        raise ValidationError(scene_id, 'missing `status`')
    if value not in ('active', 'activating', 'inactive'):
        raise ValidationError(scene_id, 'value of `status` is ambiguous')
    return value == 'active'


def _extract_bands(scene_id: str, feature: dict) -> (str, str):
    bands = feature['properties'].get('bands')
    if bands is None:
        raise ValidationError(scene_id, 'missing `bands`')
    try:
        coastal = bands['coastal'].strip()
    except:
        raise ValidationError(scene_id, 'value of `bands.coastal` is not valid')
    try:
        swir1 = bands['swir1'].strip()
    except:
        raise ValidationError(scene_id, 'value of `bands.swir1` is not valid')
    return coastal, swir1


def _extract_capture_date(scene_id: str, feature: dict) -> datetime:
    value = feature['properties'].get('acquiredDate')
    if value is None:
        raise ValidationError(scene_id, 'missing `acquiredDate`')
    try:
        value = dateutil.parser.parse(value)
    except Exception as err:
        raise ValidationError(scene_id, 'could not parse `acquiredDate`: ({})'.format(err))
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


def _save_to_database(scene: Scene):
    log = logging.getLogger(__name__)
    conn = db.get_connection()
    try:
        db.scenes.insert(
            conn,
            scene_id=scene.id,
            captured_on=scene.capture_date,
            catalog_uri=scene.uri,
            cloud_cover=scene.cloud_cover,
            geometry=scene.geometry,
            resolution=scene.resolution,
            sensor_name=scene.sensor_name,
        )
    except db.DatabaseError as err:
        log.error('Could not save scene to database')
        db.print_diagnostics(err)
        raise
    finally:
        conn.close()


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
