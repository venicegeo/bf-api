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
import math
import re
from datetime import datetime
from typing import Optional

import dateutil.parser
import requests

from bfapi import db
from bfapi.config import CATALOG, DOMAIN


PATTERN_SCENE_ID = re.compile(r'^(planetscope|rapideye):[\w_-]+$')
PLATFORM_PLANETSCOPE = 'planetscope'
PLATFORM_RAPIDEYE = 'rapideye'
STATUS_ACTIVE = 'active'
STATUS_ACTIVATING = 'activating'
STATUS_INACTIVE = 'inactive'


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
            platform: str,
            resolution: int,
            scene_id: str,
            sensor_name: str,
            status: str,
            tide: float,
            tide_min: float,
            tide_max: float,
            uri: str):
        self.capture_date = capture_date
        self.cloud_cover = cloud_cover
        self.id = scene_id
        self.geometry = geometry
        self.geotiff_coastal = geotiff_coastal
        self.geotiff_multispectral = geotiff_multispectral
        self.geotiff_swir1 = geotiff_swir1
        self.platform = platform
        self.resolution = resolution
        self.sensor_name = sensor_name
        self.status = status
        self.tide = tide
        self.tide_min = tide_min
        self.tide_max = tide_max
        self.uri = uri


#
# Actions
#

def activate(scene: Scene, planet_api_key: str, user_id: str) -> Optional[str]:
    log = logging.getLogger(__name__)
    log.info('Scenes service activate scene', action='service scenes activate scene')

    if scene.status == STATUS_ACTIVE:
        return scene.geotiff_multispectral
    elif scene.status == STATUS_ACTIVATING:
        return None

    # Request activation
    platform, external_id = _parse_scene_id(scene.id)

    activation_url = 'https://{}/planet/activate/{}/{}'.format(CATALOG, platform, external_id)
    log.info('Activating `%s`', scene.id, actor=user_id, action='activate scene', actee=scene.id)
    try:
        log.debug('Requesting activation; url=`%s`', activation_url)
        response = requests.get(
            activation_url,
            params={
                'PL_API_KEY': planet_api_key,
            }
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise CatalogError()
    except requests.HTTPError as err:
        log.debug('Http error on scene activation; status code `%d`', err.response.status_code)
        status_code = err.response.status_code
        if status_code == 401:
            raise NotPermitted("activate scene")
        if status_code == 404:
            raise NotFound(scene.id)
        raise CatalogError()


def create_download_url(scene_id: str, planet_api_key: str = '') -> str:
    # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
    # FIXME -- hopefully this endpoint can move into the IA Broker eventually
    log = logging.getLogger(__name__)
    log.info('Scenes service create download url', action='service scenes create download url')
    return 'https://bf-api.{}/v0/scene/{}.TIF?planet_api_key={}'.format(
        DOMAIN,
        scene_id,
        planet_api_key,
    )
    # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK


def get(scene_id: str, planet_api_key: str, *, with_tides: bool = True) -> Scene:
    log = logging.getLogger(__name__)
    log.info('Scenes service get scene', action='service scenes get scene')

    platform, external_id = _parse_scene_id(scene_id)

    uri = 'https://{}/planet/{}/{}'.format(CATALOG, platform, external_id)
    log.info('Fetching `%s`', uri, action='fetch scene metadata', actee=scene_id)
    try:
        response = requests.get(
            uri,
            params={
                'PL_API_KEY': planet_api_key,
                'tides': with_tides,
            }
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise CatalogError()
    except requests.HTTPError as err:
        log.debug('Http error on scene get; status code `%d`', err.response.status_code)
        status_code = err.response.status_code
        if status_code == 401:
            raise NotPermitted("fetch scene metadata")
        if status_code == 404:
            raise NotFound(scene_id)
        raise CatalogError()

    feature = response.json()

    status = _extract_status(scene_id, feature)

    geotiff_multispectral = feature['properties'].get('location')
    if status == STATUS_ACTIVE and not geotiff_multispectral:
        raise ValidationError(scene_id, 'Scene is activated but missing GeoTIFF URL')

    scene = Scene(
        scene_id=scene_id,
        uri=uri,
        capture_date=_extract_capture_date(scene_id, feature),
        cloud_cover=_extract_cloud_cover(scene_id, feature),
        geometry=_extract_geometry(scene_id, feature),
        geotiff_multispectral=geotiff_multispectral,
        platform=platform,
        resolution=_extract_resolution(scene_id, feature),
        sensor_name=_extract_sensor_name(scene_id, feature),
        status=status,
        tide=_extract_tide(scene_id, feature),
        tide_min=_extract_tide_min(scene_id, feature),
        tide_max=_extract_tide_max(scene_id, feature),
    )

    _save_to_database(scene)
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


def _extract_cloud_cover(scene_id: str, feature: dict) -> float:
    value = feature['properties'].get('cloudCover')
    if value is None:
        raise ValidationError(scene_id, 'missing `cloudCover`')
    try:
        value = round(value, 2)
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
        value = int(math.ceil(value))
    except:
        raise ValidationError(scene_id, '`resolution` is not an int')
    return value


def _extract_sensor_name(scene_id: str, feature: dict) -> str:
    value = feature['properties'].get('sensorName')
    if value is None:
        raise ValidationError(scene_id, 'missing `sensorName`')
    return value.strip()


def _extract_status(scene_id: str, feature) -> str:
    value = feature['properties'].get('status')
    if value is None:
        raise ValidationError(scene_id, 'missing `status`')
    if value not in (STATUS_ACTIVE, STATUS_ACTIVATING, STATUS_INACTIVE):
        raise ValidationError(scene_id, 'value of `status` is ambiguous')
    return value


def _extract_tide(scene_id: str, feature: dict) -> float:
    value = feature['properties'].get('CurrentTide')
    if value is not None:
        try:
            value = round(value, 5)
        except:
            raise ValidationError(scene_id, '`CurrentTide` is not a float')
    return value


def _extract_tide_min(scene_id: str, feature: dict) -> float:
    value = feature['properties'].get('24hrMinTide')
    if value is not None:
        try:
            value = round(value, 5)
        except:
            raise ValidationError(scene_id, '`24hrMinTide` is not a float')
    return value


def _extract_tide_max(scene_id: str, feature: dict) -> float:
    value = feature['properties'].get('24hrMaxTide')
    if value is not None:
        try:
            value = round(value, 5)
        except:
            raise ValidationError(scene_id, '`24hrMaxTide` is not a float')
    return value


def _parse_scene_id(scene_id) -> (str, str):
    if not PATTERN_SCENE_ID.match(scene_id):
        raise MalformedSceneID(scene_id)
    return scene_id.split(':', 1)


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
        log.error('Could not save scene `%s` to database', scene.id)
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


class NotPermitted(Exception):
    def __init__(self, action:str):
        super().__init__('user is not permitted to {}'.format(action))


class ValidationError(Exception):
    def __init__(self, scene_id: str, message: str):
        super().__init__('scene `{}` has invalid metadata: {}'.format(scene_id, message))
        self.scene_id = scene_id
