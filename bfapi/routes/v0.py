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
from json import JSONDecodeError

import dateutil.parser
import dateutil.tz
import flask
import json

from bfapi.config import CATALOG, GEOSERVER_HOST
from bfapi.db import DatabaseError

from bfapi.service import algorithms as _algorithms, jobs as _jobs, productlines as _productlines, JWT_Transcipher as JWT_service

#
# Algorithms
#

#Audit Log Required: data access
def get_algorithm(service_id: str):
    try:
        algorithm = _algorithms.get(service_id)
    except _algorithms.NotFound:
        return 'Algorithm not found', 404
    return flask.jsonify({
        'algorithm': algorithm.serialize(),
    })

#Audit Log Required: data access
def list_algorithms():
    algorithms = _algorithms.list_all()
    log = logging.getLogger(__name__)
    log.info('Attempting access json', extra={'actor': 'system', 'actee': 'system', 'action': 'data query'})
    return flask.jsonify({
        'algorithms': [a.serialize() for a in algorithms],
    })

#
# JWT
#
#Audit Log Required: action preformed
def encrypt_JWT():
    log = logging.getLogger(__name__)
    try:
        log.info('Attempting access json', extra={'actor': 'system', 'actee': 'system', 'action': 'data query'})
        payload = flask.request.get_json()
    except JSONDecodeError:
        log.info('Attempting access json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'invalid json'})
        return 'Invalid input: request body must be a JSON object', 400
    except ValidationError as err:
        log.info('Attempting access json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'invalid json'})
        return 'Invalid input: {}'.format(err), 400
    try:
        log.info('Attempting to encrypt json', extra={'actor': 'system', 'actee': 'system', 'action': 'encrypting'})
        encryptedJWT = JWT_service.encrypt(payload)
    except ValidationError as err:
        log.info('Attempting json encryption failed', extra={'actor': 'system', 'actee': 'system', 'action': 'internal error'})
        return 'Unable to encrypt'.format(err), 400
    return encryptedJWT, 201

#Audit Log Required: action preformed
def decrypt_JWT():
    log = logging.getLogger(__name__)
    try:
        log.info('Attempting access json', extra={'actor': 'system', 'actee': 'system', 'action': 'data access'})
        bodyJSON = flask.request.get_json()
        JWT = _get_string(bodyJSON, 'JWT')
    except JSONDecodeError:
        log.info('Attempting access json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'decode error'})
        return 'Invalid input: request body must be a JSON object', 400
    except ValidationError as err:
        log.info('Attempting access json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'validation error'})
        return 'Invalid input: {}'.format(err), 400
    try:
        log.info('Attempting decryption', extra={'actor': 'system', 'actee': 'system', 'action': 'decrypt'})
        decryptedJWT=JWT_service.decrypt(JWT)
    except JWTDecryptError:
        log.info('Attempting decryption failed', extra={'actor': 'system', 'actee': 'system', 'action': 'internal error'})
        return 

    return flask.jsonify(decryptedJWT), 201

#
# Jobs
#
#Audit Log Required: data creation attempt
def create_job():
    log = logging.getLogger(__name__)
    try:
        payload = flask.request.get_json()
        job_name = _get_string(payload, 'name', max_length=100)
        planet_api_key = _get_string(payload, 'planet_api_key', max_length=64)
        service_id = _get_string(payload, 'algorithm_id', max_length=64)
        scene_id = _get_string(payload, 'scene_id', max_length=64)
        log.info('Attempting create job from json', extra={'actor': 'system', 'actee': 'system', 'action': 'create data'})
    except JSONDecodeError:
        log.info('Attempting create job from json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'json error'})
        return 'Invalid input: request body must be a JSON object', 400
    except ValidationError as err:
        log.info('Attempting create job from json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'validation error'})
        return 'Invalid input: {}'.format(err), 400

    try:
        log.info('Attempting create job record', extra={'actor': 'system', 'actee': 'system', 'action': 'create data'})
        record = _jobs.create(
            user_id=flask.request.user.user_id,
            service_id=service_id,
            scene_id=scene_id,
            job_name=job_name.strip(),
            planet_api_key=planet_api_key,
        )
    except _jobs.PreprocessingError as err:
        log.info('Attempting create job record failed', extra={'actor': 'system', 'actee': 'system', 'action': 'proccessing error'})
        return 'Cannot execute: {}'.format(err), 500
    except DatabaseError:
        log.info('Attempting create job record failed', extra={'actor': 'system', 'actee': 'system', 'action': 'database error'})
        return 'A database error prevents job execution', 500
    return flask.jsonify({
        'job': record.serialize(),
    }), 201

#Audit Log Required: data access
def download_geojson(job_id: str):
    log = logging.getLogger(__name__)
    try:
        log.info('Attempting download json', extra={'actor': 'system', 'actee': 'system', 'action': 'data download'})
        detections = _jobs.get_detections(job_id)
    except _jobs.NotFound:
        log.info('Attempting download json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'not found'})
        return 'Job not found', 404
    except _jobs.Error as err:
        log.info('Attempting download json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'unable to download'})
        return 'Cannot download: {}'.format(err), 500
    except DatabaseError:
        log.info('Attempting download json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'database error'})
        return 'A database error prevents detection download', 500
    return detections, 200, {
        'Content-Type': 'application/vnd.geo+json',
    }

#Audit Log Required: data removed
def forget_job(job_id: str):
    log = logging.getLogger(__name__)
    try:
        log.info('Attempting forget job', extra={'actor': user_id, 'actee': 'system', 'action': 'delete data'})
        _jobs.forget(flask.request.user.user_id, job_id)
    except _jobs.NotFound:
        log.info('Attempting forget job failed', extra={'actor': 'system', 'actee': 'system', 'action': 'job not found'})
        return 'Job not found', 404
    return 'Forgot {}'.format(job_id), 200

#Audit Log Required: data access
def list_jobs():
    log = logging.getLogger(__name__)
    log.info('Attempting list jobs', extra={'actor': user_id, 'actee': 'system', 'action': 'query data'})
    jobs = _jobs.get_all(flask.request.user.user_id)
    return flask.jsonify({
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        },
    })

#Audit Log Required: data access
def list_jobs_for_productline(productline_id: str):
    try:
        log = logging.getLogger(__name__)
        log.info('Attempting list jobs for productline ', extra={'actor': 'system', 'actee': 'system', 'action': 'query data'})
        since = dateutil.parser.parse(
            flask.request.args.get('since', '1970-01-01', type=str),
        ).replace(tzinfo=dateutil.tz.tzutc())  # type: datetime
    except ValueError:
        log.info('Attempting list jobs for productline failed', extra={'actor': 'system', 'actee': 'system', 'action': 'value error'})
        return 'Invalid input: `since` value cannot be parsed as a valid date', 400
    jobs = _jobs.get_by_productline(productline_id, since)
    return flask.jsonify({
        'productline_id': productline_id,
        'since': since.isoformat(),
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        },
    })

#Audit Log Required: data access
def list_jobs_for_scene(scene_id: str):
    log = logging.getLogger(__name__)
    jobs = _jobs.get_by_scene(scene_id)
    log.info('Attempting list jobs for scene', extra={'actor': 'system', 'actee': 'system', 'action': 'query data'})
    return flask.jsonify({
        'scene_id': scene_id,
        'jobs': {
            'type': 'FeatureCollection',
            'features': [j.serialize() for j in jobs],
        }
    })

#Audit Log Required: data access
def get_job(job_id: str):
    log = logging.getLogger(__name__)
    try:
        log.info('Attempting get job', extra={'actor': 'system', 'actee': 'system', 'action': 'query data'})
        record = _jobs.get(flask.request.user.user_id, job_id)
    except _jobs.NotFound:
        log.info('Attempting get job failed', extra={'actor': 'system', 'actee': 'system', 'action': 'job not found'})
        return 'Job not found', 404
    return flask.jsonify({
        'job': record.serialize(),
    })


#
# Product Lines
#
#Audit Log Required: data created
def create_productline():
    log = logging.getLogger(__name__)
    try:
        log.info('Attempting create productline json', extra={'actor': 'system', 'actee': 'system', 'action': 'create data'})
        payload = flask.request.get_json()
        algorithm_id = _get_string(payload, 'algorithm_id', max_length=100)
        category = _get_string(payload, 'category', nullable=True, max_length=64)
        min_x = _get_number(payload, 'min_x', min_value=-180, max_value=180)
        min_y = _get_number(payload, 'min_y', min_value=-90, max_value=90)
        max_x = _get_number(payload, 'max_x', min_value=-180, max_value=180)
        max_y = _get_number(payload, 'max_y', min_value=-90, max_value=90)
        max_cloud_cover = int(_get_number(payload, 'max_cloud_cover', min_value=0, max_value=100))
        name = _get_string(payload, 'name', max_length=100)
        spatial_filter_id = _get_string(payload, 'spatial_filter_id', nullable=True, max_length=64)
        start_on = _get_datetime(payload, 'start_on')
        stop_on = _get_datetime(payload, 'stop_on', nullable=True)
    except JSONDecodeError:
        log.info('Attempting create productline json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'json decode error'})
        return 'Invalid input: request body must be a JSON object', 400
    except ValidationError as err:
        log.info('Attempting create productline json failed', extra={'actor': 'system', 'actee': 'system', 'action': 'format error'})
        return 'Invalid input: {}'.format(err), 400

    try:
        log.info('Attempting create productline record', extra={'actor': 'system', 'actee': 'system', 'action': 'create data'})
        productline = _productlines.create_productline(
            algorithm_id=algorithm_id,
            bbox=(min_x, min_y, max_x, max_y),
            category=category,
            max_cloud_cover=max_cloud_cover,
            name=name,
            spatial_filter_id=spatial_filter_id,
            start_on=start_on.date(),
            stop_on=stop_on.date() if stop_on else None,
            user_id=flask.request.user.user_id,
        )
    except _algorithms.NotFound as err:
        log.info('Attempting create productline record failed', extra={'actor': 'system', 'actee': 'system', 'action': 'algorithm not found'})
        return 'Algorithm {} does not exist'.format(err.service_id), 500
    except DatabaseError:
        log.info('Attempting create productline record failed', extra={'actor': 'system', 'actee': 'system', 'action': 'database error'})
        return 'A database error prevents product line creation', 500
    return flask.jsonify({
        'productline': productline.serialize(),
    }), 201

#Audit Log Required: data deleted
def delete_productline(productline_id: str):
    log = logging.getLogger(__name__)
    log.info('Attempting delete productline', extra={'actor': user_id, 'actee': 'system', 'action': 'data delete'})
    user_id = flask.request.user.user_id
    try:
        _productlines.delete_productline(user_id, productline_id)
    except DatabaseError:
        log.info('Attempting delete productline failed', extra={'actor': 'system', 'actee': 'system', 'action': 'database error'})
        return 'A database error prevents deletion of this product line', 404
    except _productlines.NotFound:
        log.info('Attempting delete productline failed', extra={'actor': 'system', 'actee': 'system', 'action': 'productline not found'})
        return 'Product line not found', 404
    except PermissionError:
        log.info('Attempting delete productline failed', extra={'actor': 'system', 'actee': 'system', 'action': 'permissions error'})
        return 'User `{}` does not have permission to delete this product line'.format(user_id), 403
    return 'Deleted product line {}'.format(productline_id), 200

#Audit Log Required: data access
def list_productlines():
    log = logging.getLogger(__name__)
    productlines = _productlines.get_all()
    log.info('Attempting get productlines list', extra={'actor': 'system', 'actee': 'system', 'action': 'data query'})
    return flask.jsonify({
        'productlines': {
            'type': 'FeatureCollection',
            'features': [p.serialize() for p in productlines],
        },
    })


#
# Profile
#
#Audit Log Required: data access
def get_user_data():
    log = logging.getLogger(__name__)
    log.info('Attempting get user data', extra={'actor': 'system', 'actee': 'system', 'action': 'data query'})
    return flask.jsonify({
        'profile': {
            'username': flask.request.user.user_id,
            'api_key': flask.request.user.api_key,
            'joined_on': flask.request.user.created_on,
        },
        'services': {
            'catalog': 'https://{}'.format(CATALOG),
            'wms_server': 'https://{}/geoserver/wms'.format(GEOSERVER_HOST),
        },
    })

#
# Scenes
#

# HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
# FIXME -- hopefully this can move into the IA Broker eventually
def forward_to_geotiff(scene_id: str):
    log = logging.getLogger(__name__)
    log.info('Attempting foward to geotiff', extra={'actor': 'system', 'actee': 'system', 'action': 'data manipulation'})
    planet_api_key = flask.request.args.get('planet_api_key')
    if not planet_api_key:
        log.info('Attempting foward to geotiff failed', extra={'actor': 'system', 'actee': 'system', 'action': 'missing api key'})
        return 'Missing `planet_api_key` parameter', 400

    try:
        scene = _scenes.get(scene_id, planet_api_key)
        geotiff_url = _scenes.activate(scene, planet_api_key)
    except _scenes.NotFound:
        log.info('Attempting foward to geotiff failed', extra={'actor': 'system', 'actee': 'system', 'action': 'scene not found'})
        return 'Cannot download: Scene `{}` not found'.format(scene_id), 404
    except (_scenes.CatalogError,
            _scenes.MalformedSceneID) as err:
        log.info('Attempting foward to geotiff failed', extra={'actor': 'system', 'actee': 'system', 'action': 'download error'})
        return 'Cannot download: {}'.format(err), 500

    if geotiff_url:
        return flask.redirect(geotiff_url)

    return """
        <h1>GeoTIFF for <code>{scene_id}</code> is activating</h1>
        <p>
            We're still requesting the GeoTIFF for this scene for you.  Your
            browser will automatically be redirected to the GeoTIFF file when it
            is ready. <strong>If this takes longer than an hour, please contact
            the Beachfront team for technical support.</strong>
        </p>

        <p>
            Your wait time so far is: <code class="elapsed">NN duration</code>.
        </p>

        <script>
            setTimeout(location.reload.bind(location), 30000)

            var t = sessionStorage.getItem(location.href)
            if (!t) {{
                t = Date.now()
                sessionStorage.setItem(location.href, t)
            }}

            // Update thingy
            var seconds = Math.ceil((Date.now() - t) / 1000)
            var timeElapsed = seconds < 60 ? seconds + ' second(s)' : Math.floor(seconds / 60) + ' minute(s)'
            document.querySelector('.elapsed').textContent = timeElapsed
        </script>
        <style>
            body {{
                margin: 5em;
                font: 18px sans-serif;
                line-height: 1.75em;
            }}
            .elapsed {{
                background-color: #eee;
                color: #555;
                padding: .3em;
                margin: 0 .25em;
                font-weight: bold;
            }}
        </style>
    """.format(scene_id=scene_id), 202, {
        'Content-Type': 'text/html',
    }
# HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK


#
# Helpers
#
#Audit Log Required: data access
def _get_datetime(d: dict, key: str, *, nullable: bool = False) -> datetime:
    if key not in d:
        raise ValidationError('`{}` is missing'.format(key))
    value = d.get(key)
    if nullable and not value:
        return None
    try:
        value = dateutil.parser.parse(value)
    except:
        raise ValidationError('`{}` must be a valid timestamp'.format(key))
    return value

#Audit Log Required: data access
def _get_number(d: dict, key: str, *, min_value: int = None, max_value: int = None):
    if key not in d:
        raise ValidationError('`{}` is missing'.format(key))
    value = d.get(key)
    if not isinstance(value, int) and not isinstance(value, float):
        raise ValidationError('`{}` must be a number'.format(key))
    if min_value is not None and value < min_value or max_value is not None and value > max_value:
        raise ValidationError('`{}` must be a number between {} and {}'.format(key, min_value, max_value))
    return value

#Audit Log Required: data access
def _get_string(d: dict, key: str, *, nullable: bool = False, min_length: int = 1, max_length: int = 256):
    if key not in d:
        raise ValidationError('`{}` is missing'.format(key))
    value = d.get(key)
    if nullable and value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError('`{}` must be a string'.format(key))
    value = value.strip()
    if len(value) > max_length or len(value) < min_length:
        raise ValidationError('`{}` must be a string of {}–{} characters'.format(key, min_length, max_length))
    return value


#
# Errors
#

class ValidationError(Exception):
    pass
