# Copyright 2017, RadiantBlue Technologies, Inc.
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

import requests

from bfapi.config import GPKG_CONVERTER, PIAZZA_API_KEY

TIMEOUT = 24

def convert_geojson_to_geopackage(geojson: str) -> bytes:
    log = logging.getLogger(__name__)
    log.info('Convert GeoJSON->GeoPackage "%s"', piazza_id action=' service geopackage convert')

    try:
        response = requests.get(
            'https://{}/convert'.format(
                GPKG_CONVERTER,
            ),
            timeout=TIMEOUT,
            data=geojson,
        )

        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoPackage converter: %s', err)
        raise GeoPackageError()
    except requests.HTTPError as err:
        message = 'Cannot convert Piazza object `%s`: HTTP %d on %s to %s' % (
                  piazza_id,
                  err.response.status_code,
                  err.request.method,
                  err.request.url)
        log.error(message)
        raise GeoPackageError(message)
    except response.headers.get('content-type') != 'application/x-sqlite3':
        message = 'Unexpected content type from GeoPackage converter: `%s`' % response.headers.get('content-type')
        log.error(message)
        raise GeoPackageError(message)

    return response.content

#
# Errors
#

class GeoPackageError(Exception):
    def __init__(self, message: str = 'error communicating with GeoPackage converter'):
        super().__init__(message)
