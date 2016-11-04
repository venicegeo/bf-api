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

import base64
import logging

import requests

from bfapi.config import GEOSERVER_HOST, GEOSERVER_USERNAME, GEOSERVER_PASSWORD

DETECTIONS_LAYER_ID = 'bfdetections'
DETECTIONS_STYLE_ID = 'bfdetections'
TIMEOUT = 24


def install_if_needed():
    log = logging.getLogger(__name__)
    log.info('Checking to see if installation is required')

    is_installed = True

    if not layer_exists(DETECTIONS_LAYER_ID):
        is_installed = False
        install_layer(DETECTIONS_LAYER_ID)

    if not style_exists(DETECTIONS_STYLE_ID):
        is_installed = False
        install_style(DETECTIONS_STYLE_ID)

    if is_installed:
        log.info('GeoServer components exist and will not be reinstalled')
    else:
        log.info('Installation complete!')


def install_layer(layer_id: str):
    log = logging.getLogger(__name__)
    log.info('Installing `%s`', layer_id)
    try:
        response = requests.post(
            'http://{host}/geoserver/rest/workspaces/{ws}/datastores/{ds}/featuretypes'.format(  # FIXME -- http please
                host=GEOSERVER_HOST,
                ws='piazza',  # FIXME -- autodetect?
                ds='piazza',  # FIXME -- autodetect?
            ),
            timeout=TIMEOUT,
            headers={
                'Authorization': _generate_auth_header(),
                'Content-Type': 'application/xml',
            },
            data=r"""
                <featureType>
                    <name>{layer_id}</name>
                    <title>Beachfront Detections</title>
                    <srs>EPSG:4326</srs>
                    <nativeBoundingBox>
                        <minx>-180.0</minx>
                        <maxx>180.0</maxx>
                        <miny>-90.0</miny>
                        <maxy>90.0</maxy>
                    </nativeBoundingBox>
                    <metadata>
                        <entry key="JDBC_VIRTUAL_TABLE">
                            <virtualTable>
                                <name>{layer_id}</name>
                                <sql>
                                    SELECT * FROM __beachfront__geoserver
                                    WHERE ('%sceneid%' = '' AND '%jobid%' = '')
                                       OR (job_id = '%jobid%')
                                       OR (scene_id = '%sceneid%')</sql>
                                <escapeSql>false</escapeSql>
                                <keyColumn>job_id</keyColumn>
                                <geometry>
                                    <name>geometry</name>
                                    <type>Geometry</type>
                                    <srid>4326</srid>
                                </geometry>
                                <parameter>
                                    <name>jobid</name>
                                    <regexpValidator>^(%|[a-f0-9]{{8}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{4}}-[a-f0-9]{{12}})$</regexpValidator>
                                </parameter>
                                <parameter>
                                    <name>sceneid</name>
                                    <regexpValidator>^\w+:\w+$</regexpValidator>
                                </parameter>
                            </virtualTable>
                        </entry>
                        <entry key="time">
                            <dimensionInfo>
                                <enabled>true</enabled>
                                <attribute>captured_on</attribute>
                                <presentation>CONTINUOUS_INTERVAL</presentation>
                                <units>ISO8601</units>
                                <defaultValue>
                                    <strategy>FIXED</strategy>
                                    <referenceValue>P1Y/PRESENT</referenceValue>
                                </defaultValue>
                            </dimensionInfo>
                        </entry>
                    </metadata>
                </featureType>
            """.strip().format(layer_id=layer_id),
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise GeoServerError()
    except requests.HTTPError as err:
        log.error('Cannot create layer `%s`: HTTP %d on %s to %s',
                  layer_id,
                  err.response.status_code,
                  err.request.method,
                  err.request.url)
        raise GeoServerError()


def install_style(style_id: str):
    log = logging.getLogger(__name__)
    log.info('Installing `%s`', style_id)
    try:
        response = requests.post(
            'http://{}/geoserver/rest/styles'.format(  # FIXME -- https please?
                GEOSERVER_HOST,
            ),
            data="""
                <StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld">
                  <NamedLayer>
                    <UserStyle>
                      <FeatureTypeStyle>
                        <Rule>
                          <LineSymbolizer>
                            <Stroke>
                              <CssParameter name="stroke">#FF00FF</CssParameter>
                            </Stroke>
                          </LineSymbolizer>
                        </Rule>
                      </FeatureTypeStyle>
                    </UserStyle>
                  </NamedLayer>
                </StyledLayerDescriptor>
            """.strip(),
            timeout=TIMEOUT,
            headers={
                'Authorization': _generate_auth_header(),
                'Content-Type': 'application/vnd.ogc.sld+xml',
            },
            params={
                'name': style_id,
            },
        )
        response.raise_for_status()
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise GeoServerError()
    except requests.HTTPError as err:
        log.error('Cannot create style `%s`: HTTP %d on %s to %s',
                  style_id,
                  err.response.status_code,
                  err.request.method,
                  err.request.url)
        raise GeoServerError()


def layer_exists(layer_id: str) -> bool:
    log = logging.getLogger(__name__)
    try:
        response = requests.get(
            'http://{}/geoserver/rest/layers/{}'.format(  # FIXME -- https please
                GEOSERVER_HOST,
                layer_id,
            ),
            timeout=TIMEOUT,
            headers={
                'Authorization': _generate_auth_header(),
            },
        )
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise GeoServerError()
    return response.status_code == 200


def style_exists(style_id: str) -> bool:
    log = logging.getLogger(__name__)
    try:
        response = requests.get(
            'http://{}/geoserver/rest/styles/{}'.format(  # FIXME -- https please
                GEOSERVER_HOST,
                style_id,
            ),
            timeout=TIMEOUT,
            headers={
                'Authorization': _generate_auth_header(),
            },
        )
    except requests.ConnectionError as err:
        log.error('Cannot communicate with GeoServer: %s', err)
        raise GeoServerError()
    return response.status_code == 200


#
# Internals
#

def _generate_auth_header():
    return 'Basic ' + base64.b64encode('{}:{}'.format(GEOSERVER_USERNAME, GEOSERVER_PASSWORD).encode()).decode()


#
# Errors
#

class GeoServerError(Exception):
    def __init__(self, message: str = 'error communicating with GeoServer'):
        super().__init__(message)