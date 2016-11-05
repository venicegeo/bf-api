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
import unittest.mock

import requests_mock as rm
from requests import ConnectionError

from test import helpers

from bfapi.db import DatabaseError
from bfapi.service import scenes


@rm.Mocker()
class GetSceneTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.scenes')
        self._logger.disabled = True

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_calls_correct_url(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scenes.get('landsat:LC80110632016220LGN00')
        self.assertEqual('https://pzsvc-image-catalog.localhost/image/landsat:LC80110632016220LGN00',
                         m.request_history[0].url)

    def test_fetches_scenes(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = scenes.get('landsat:LC80110632016220LGN00')
        self.assertIsInstance(scene, scenes.Scene)

    def test_yields_correct_capture_date(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = scenes.get('landsat:LC80110632016220LGN00')
        self.assertEqual('2016-08-07T15:33:42.572449+00:00',
                         scene.capture_date.isoformat())

    def test_yields_correct_bands(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = scenes.get('landsat:LC80110632016220LGN00')
        self.assertSetEqual({'blue', 'cirrus', 'coastal', 'green', 'nir', 'panchromatic', 'red', 'swir1', 'swir2',
                             'tirs1', 'tirs2'},
                            set(scene.bands.keys()))

    def test_yields_correct_cloud_cover(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = scenes.get('landsat:LC80110632016220LGN00')
        self.assertEqual(1.47, scene.cloud_cover)

    def test_yields_correct_id(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = scenes.get('landsat:LC80110632016220LGN00')
        self.assertEqual('landsat:LC80110632016220LGN00', scene.id)

    def test_yields_correct_geometry(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = scenes.get('landsat:LC80110632016220LGN00')
        self.assertIsInstance(scene.geometry, dict)
        self.assertIsInstance(scene.geometry.get('coordinates'), list)
        self.assertEqual([[[-81.5725334896228, -3.29632263428811], [-79.934112104967, -3.64597257671337],
                           [-80.3035877737851, -5.38806769101045], [-81.9453446162527, -5.03306405829352],
                           [-81.5725334896228, -3.29632263428811]]],
                         scene.geometry.get('coordinates'))

    def test_yields_correct_resolution(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = scenes.get('landsat:LC80110632016220LGN00')
        self.assertEqual(30, scene.resolution)

    def test_yields_correct_sensor_name(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = scenes.get('landsat:LC80110632016220LGN00')
        self.assertEqual('Landsat8', scene.sensor_name)

    def test_yields_correct_uri(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = scenes.get('landsat:LC80110632016220LGN00')
        self.assertEqual('https://pzsvc-image-catalog.localhost/image/landsat:LC80110632016220LGN00',
                         scene.uri)

    def test_throws_if_catalog_is_unreachable(self, _):
        with unittest.mock.patch('requests.get') as stub:
            stub.side_effect = ConnectionError()
            with self.assertRaises(scenes.CatalogError):
                scenes.get('landsat:LC80110632016220LGN00')

    def test_gracefully_handles_catalog_http_errors(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', status_code=500, text='oh noes')
        with self.assertRaises(scenes.CatalogError):
            scenes.get('landsat:LC80110632016220LGN00')

    def test_throws_if_scene_does_not_exist(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', status_code=404, text=RESPONSE_SCENE_NOT_FOUND)
        with self.assertRaises(scenes.NotFound):
            scenes.get('landsat:LC80110632016220LGN00')

    def test_throws_if_scene_id_is_malformed(self, _):
        with self.assertRaises(scenes.MalformedSceneID):
            scenes.get('lolwut')

    def test_saves_scene_to_database(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scenes.get('landsat:LC80110632016220LGN00')
        self.assertTrue(self._mockdb.executed)

    def test_gracefully_handles_database_errors(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        self._mockdb.raise_on_execute()
        with self.assertRaises(DatabaseError):
            scenes.get('landsat:LC80110632016220LGN00')


@rm.Mocker()
@unittest.mock.patch('bfapi.piazza.to_auth_header', return_value='Basic Og==')
class GetEventTypeIDTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.service.scenes')
        self._logger.disabled = True

    def tearDown(self):
        self._logger.disabled = False

    def test_calls_correct_url(self, m: rm.Mocker, _):
        m.get('/eventTypeID', text=RESPONSE_EVENT_TYPE_ID)
        scenes.get_event_type_id()
        self.assertEqual(
            'https://pzsvc-image-catalog.localhost/eventTypeID?pzGateway=https%3A%2F%2Fpz-gateway.localhost',
            m.request_history[0].url,
        )

    def test_passes_correct_headers(self, m: rm.Mocker, _):
        m.get('/eventTypeID', text=RESPONSE_EVENT_TYPE_ID)
        scenes.get_event_type_id()
        self.assertEqual('Basic Og==', m.request_history[0].headers['Authorization'])

    def test_returns_event_type_id(self, m: rm.Mocker, _):
        m.get('/eventTypeID', text=RESPONSE_EVENT_TYPE_ID)
        event_type_id = scenes.get_event_type_id()
        self.assertEqual(RESPONSE_EVENT_TYPE_ID, event_type_id)

    def test_gracefully_handles_http_errors(self, m: rm.Mocker, _):
        m.get('/eventTypeID', status_code=500, text='oh noes')
        with self.assertRaises(scenes.CatalogError):
            scenes.get_event_type_id()

    def test_throws_if_event_type_id_is_malformed(self, m: rm.Mocker, _):
        m.get('/eventTypeID', text='lolwut')
        with self.assertRaises(scenes.CatalogError):
            scenes.get_event_type_id()


#
# Fixtures
#

RESPONSE_EVENT_TYPE_ID = 'ffffffff-ffff-ffff-ffff-ffffffffffff'

RESPONSE_SCENE_NOT_FOUND = (
    'Unable to retrieve metadata for landsat:LC80110632016220LGN00: redis: nil even using wildcard search'
)

RESPONSE_SCENE = """{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [
          -81.5725334896228,
          -3.29632263428811
        ],
        [
          -79.934112104967,
          -3.64597257671337
        ],
        [
          -80.3035877737851,
          -5.38806769101045
        ],
        [
          -81.9453446162527,
          -5.03306405829352
        ],
        [
          -81.5725334896228,
          -3.29632263428811
        ]
      ]
    ]
  },
  "properties": {
    "acquiredDate": "2016-08-07T15:33:42.572449+00:00",
    "bands": {
      "blue": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B2.TIF",
      "cirrus": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B9.TIF",
      "coastal": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B1.TIF",
      "green": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B3.TIF",
      "nir": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B5.TIF",
      "panchromatic": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B8.TIF",
      "red": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B4.TIF",
      "swir1": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B6.TIF",
      "swir2": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B7.TIF",
      "tirs1": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B10.TIF",
      "tirs2": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_B11.TIF"
    },
    "cloudCover": 1.47,
    "fileFormat": "geotiff",
    "path": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/index.html",
    "resolution": 30,
    "sensorName": "Landsat8",
    "thumb_large": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_thumb_large.jpg",
    "thumb_small": "https://landsat-pds.s3.amazonaws.com/L8/011/063/LC80110632016220LGN00/LC80110632016220LGN00_thumb_small.jpg"
  },
  "id": "landsat:LC80110632016220LGN00",
  "bbox": [
    -81.9453446162527,
    -5.38806769101045,
    -79.934112104967,
    -3.29632263428811
  ]
}
"""
