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

import psycopg2 as pg
import requests_mock as rm

from bfapi import db

from bfapi.service import scenes as service

@rm.Mocker()
@unittest.mock.patch('psycopg2.connect')
class SceneGetTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.service.scenes')
        self._logger.disabled = True

    def tearDown(self):
        self._logger.disabled = False

    def test_calls_correct_url(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        service.get('landsat:LC80110632016220LGN00')
        self.assertEqual('https://pzsvc-image-catalog.localhost/image/landsat:LC80110632016220LGN00',
                         m.request_history[0].url)

    def test_fetches_scenes(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = service.get('landsat:LC80110632016220LGN00')
        self.assertIsInstance(scene, service.Scene)

    def test_yields_correct_capture_date(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = service.get('landsat:LC80110632016220LGN00')
        self.assertEqual('2016-08-07T15:33:42.572449+00:00',
                         scene.capture_date.isoformat())

    def test_yields_correct_bands(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = service.get('landsat:LC80110632016220LGN00')
        self.assertSetEqual({'blue', 'cirrus', 'coastal', 'green', 'nir', 'panchromatic', 'red', 'swir1', 'swir2',
                             'tirs1', 'tirs2'},
                            set(scene.bands.keys()))

    def test_yields_correct_cloud_cover(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = service.get('landsat:LC80110632016220LGN00')
        self.assertEqual(1.47, scene.cloud_cover)

    def test_yields_correct_id(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = service.get('landsat:LC80110632016220LGN00')
        self.assertEqual('landsat:LC80110632016220LGN00', scene.id)

    def test_yields_correct_geometry(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = service.get('landsat:LC80110632016220LGN00')
        self.assertIsInstance(scene.geometry, dict)
        self.assertIsInstance(scene.geometry.get('coordinates'), list)
        self.assertEqual([[[-81.5725334896228, -3.29632263428811], [-79.934112104967, -3.64597257671337],
                           [-80.3035877737851, -5.38806769101045], [-81.9453446162527, -5.03306405829352],
                           [-81.5725334896228, -3.29632263428811]]],
                         scene.geometry.get('coordinates'))

    def test_yields_correct_resolution(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = service.get('landsat:LC80110632016220LGN00')
        self.assertEqual(30, scene.resolution)

    def test_yields_correct_sensor_name(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = service.get('landsat:LC80110632016220LGN00')
        self.assertEqual('Landsat8', scene.sensor_name)

    def test_yields_correct_uri(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        scene = service.get('landsat:LC80110632016220LGN00')
        self.assertEqual('https://pzsvc-image-catalog.localhost/image/landsat:LC80110632016220LGN00',
                         scene.uri)

    def test_handles_catalog_http_errors_gracefully(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', status_code=500, text='oh noes')
        with self.assertRaises(service.CatalogError):
            service.get('landsat:LC80110632016220LGN00')

    def test_throws_if_scene_does_not_exist(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', status_code=400, text=RESPONSE_SCENE_NOT_FOUND)
        with self.assertRaises(service.NotFound):
            service.get('landsat:LC80110632016220LGN00')

    # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK
    # TODO -- this can go away once Redmine #9287 is closed
    def test_throws_if_scene_does_not_exist___TEMPORARY_WORKAROUND_FOR_REDMINE_9287___(self, m: rm.Mocker, _):
        m.get('/image/landsat:LC80110632016220LGN00', status_code=400, text=RESPONSE_SCENE_NOT_FOUND)
        with self.assertRaises(service.NotFound):
            service.get('landsat:LC80110632016220LGN00')
    # HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK HACK

    def test_saves_scene_to_database(self, m: rm.Mocker, mockdb):
        m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
        service.get('landsat:LC80110632016220LGN00')
        cursor = mockdb.return_value.cursor.return_value
        self.assertTrue(cursor.execute.called)

    def test_handles_database_errors_gracefully(self, m: rm.Mocker, mockdb):
        mockdb.side_effect = db.DatabaseError(pg.OperationalError(), 'test-query')
        with self.assertRaises(service.DatabaseError):
            m.get('/image/landsat:LC80110632016220LGN00', text=RESPONSE_SCENE)
            service.get('landsat:LC80110632016220LGN00')


#
# Fixtures
#

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
