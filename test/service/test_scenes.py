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
import logging
import unittest
from datetime import datetime
from unittest.mock import patch

import requests_mock as rm
from requests import ConnectionError

from test import helpers

from bfapi.db import DatabaseError
from bfapi.service import scenes


@rm.Mocker()
class ActivateSceneTest(unittest.TestCase):
    def setUp(self):
        self._logger = logging.getLogger('bfapi.service.scenes')
        self._logger.disabled = True

    def tearDown(self):
        self._logger.disabled = False

    def create_mock(self, target_name, **kwargs):
        patcher = patch(target_name, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_activates_if_inactive(self, m: rm.Mocker):
        scene = create_scene()
        m.get('/planet/activate/planetscope/test-scene-id', text='')
        scenes.activate(scene, 'test-planet-api-key')
        self.assertEqual(1, len(m.request_history))

    def test_does_not_spam_activation_url_if_already_activating(self, m: rm.Mocker):
        scene = create_scene()
        scene.status = scenes.STATUS_ACTIVATING
        m.get('/planet/activate/planetscope/test-scene-id', text='')
        scenes.activate(scene, 'test-planet-api-key')
        self.assertEqual(0, len(m.request_history))

    def test_does_not_spam_activation_url_if_already_active(self, m: rm.Mocker):
        scene = create_scene()
        scene.status = scenes.STATUS_ACTIVE
        m.get('/planet/activate/planetscope/test-scene-id', text='')
        scenes.activate(scene, 'test-planet-api-key')
        self.assertEqual(0, len(m.request_history))

    def test_calls_correct_activation_url_for_planetscope(self, m: rm.Mocker):
        scene = create_scene()
        scene.id = 'planetscope:test-scene-id'
        m.get('/planet/activate/planetscope/test-scene-id', text='')
        scenes.activate(scene, 'test-planet-api-key')
        self.assertEqual('https://bf-ia-broker.test.localdomain/planet/activate/planetscope/test-scene-id?PL_API_KEY=test-planet-api-key',
                         m.request_history[0].url)

    def test_calls_correct_activation_url_for_rapideye(self, m: rm.Mocker):
        scene = create_scene()
        scene.id = 'rapideye:test-scene-id'
        m.get('/planet/activate/rapideye/test-scene-id', text='')
        scenes.activate(scene, 'test-planet-api-key')
        self.assertEqual('https://bf-ia-broker.test.localdomain/planet/activate/rapideye/test-scene-id?PL_API_KEY=test-planet-api-key',
                         m.request_history[0].url)

    def test_returns_multispectral_url_if_activated(self, m: rm.Mocker):
        scene = create_scene()
        scene.status = scenes.STATUS_ACTIVE
        scene.geotiff_multispectral = 'test-geotiff-multispectral-url'
        m.get('/planet/activate/planetscope/test-scene-id', text='')
        url = scenes.activate(scene, 'test-planet-api-key')
        self.assertEqual('test-geotiff-multispectral-url', url)

    def test_returns_nothing_if_activated(self, m: rm.Mocker):
        scene = create_scene()
        m.get('/planet/activate/planetscope/test-scene-id', text='')
        url = scenes.activate(scene, 'test-planet-api-key')
        self.assertIsNone(url)

    def test_throws_when_catalog_is_unreachable(self, _):
        scene = create_scene()
        with unittest.mock.patch('requests.get') as stub:
            stub.side_effect = ConnectionError()
            with self.assertRaises(scenes.CatalogError):
                scenes.activate(scene, 'test-planet-api-key')

    def test_throws_when_catalog_throws(self, m: rm.Mocker):
        scene = create_scene()
        m.get('/planet/activate/planetscope/test-scene-id', status_code=500, text='oh noes')
        with self.assertRaises(scenes.CatalogError):
            scenes.activate(scene, 'test-planet-api-key')

    def test_throws_when_scene_does_not_exist(self, m: rm.Mocker):
        scene = create_scene()
        m.get('/planet/activate/planetscope/test-scene-id', status_code=404, text='wat')
        with self.assertRaises(scenes.NotFound):
            scenes.activate(scene, 'test-planet-api-key')


class CreateDownloadURLTest(unittest.TestCase):
    def test_returns_correct_url(self):
        url = scenes.create_download_url('test-scene-id', 'test-planet-api-key')
        self.assertEqual('https://bf-api.test.localdomain/v0/scene/test-scene-id.TIF?planet_api_key=test-planet-api-key', url)

    def test_accepts_blank_planet_api_key(self):
        url = scenes.create_download_url('test-scene-id')
        self.assertEqual('https://bf-api.test.localdomain/v0/scene/test-scene-id.TIF?planet_api_key=', url)


class GetSceneTest(unittest.TestCase):
    def setUp(self):
        self._mockdb = helpers.mock_database()
        self._logger = logging.getLogger('bfapi.service.scenes')
        self._logger.disabled = True

        self.mock_requests = rm.Mocker()  # type: rm.Mocker
        self.mock_requests.start()
        self.addCleanup(self.mock_requests.stop)

    def tearDown(self):
        self._mockdb.destroy()
        self._logger.disabled = False

    def test_calls_correct_url_for_planetscope_scene(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        uri, params = self.mock_requests.request_history[0].url.split('?', 1)
        self.assertEqual('https://bf-ia-broker.test.localdomain/planet/planetscope/test-scene-id', uri)
        self.assertEqual({'PL_API_KEY=test-planet-api-key', 'tides=True'}, set(params.split('&')))

    def test_calls_correct_url_for_rapideye_scene(self):
        self.mock_requests.get('/planet/rapideye/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scenes.get('rapideye:test-scene-id', 'test-planet-api-key')
        uri, params = self.mock_requests.request_history[0].url.split('?', 1)
        self.assertEqual('https://bf-ia-broker.test.localdomain/planet/rapideye/test-scene-id', uri)
        self.assertEqual({'PL_API_KEY=test-planet-api-key', 'tides=True'}, set(params.split('&')))

    def test_fetches_scenes(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertIsInstance(scene, scenes.Scene)

    def test_returns_correct_capture_date(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertEqual('2017-01-20T00:00:00+00:00', scene.capture_date.isoformat())

    def test_returns_correct_cloud_cover(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertEqual(1.47, scene.cloud_cover)

    def test_returns_correct_id(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertEqual('planetscope:test-scene-id', scene.id)

    def test_returns_correct_geometry(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertIsInstance(scene.geometry, dict)
        self.assertIsInstance(scene.geometry.get('coordinates'), list)
        self.assertEqual([[[115.78907135188213, 26.67939763560932], [115.78653934657243, 26.905071315070465],
                           [116.01004245933433, 26.90679345550323], [115.95815780815747, 26.680701401397425],
                           [115.78907135188213, 26.67939763560932]]],
                         scene.geometry.get('coordinates'))

    def test_returns_correct_geotiff_multispectral_url_for_active_scene(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_ACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertEqual('test-location', scene.geotiff_multispectral)

    def test_returns_correct_geotiff_multispectral_url_for_inactive_scene(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertIsNone(scene.geotiff_multispectral)

    def test_returns_correct_geotiff_single_band_urls(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        # FIXME -- if Planet's API ever offers Landsat retrieval...
        self.assertIsNone(scene.geotiff_coastal)
        self.assertIsNone(scene.geotiff_swir1)

    def test_returns_correct_resolution(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertEqual(4, scene.resolution)

    def test_returns_correct_sensor_name(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertEqual('test-sensor-name', scene.sensor_name)

    def test_returns_correct_uri(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scene = scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertEqual('https://bf-ia-broker.test.localdomain/planet/planetscope/test-scene-id', scene.uri)

    def test_throws_when_catalog_is_unreachable(self):
        with unittest.mock.patch('requests.get') as stub:
            stub.side_effect = ConnectionError()
            with self.assertRaises(scenes.CatalogError):
                scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_catalog_throws(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', status_code=500, text='oh noes')
        with self.assertRaises(scenes.CatalogError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_does_not_exist(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', status_code=404, text='wat')
        with self.assertRaises(scenes.NotFound):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_id_is_malformed(self):
        malformed_ids = (
            'lolwut',
            'landsat:LC80110632016220LGN00',
            'planetnope:foobar',
        )
        for malformed_id in malformed_ids:
            with self.assertRaises(scenes.MalformedSceneID):
                scenes.get(malformed_id, 'test-planet-api-key')

    def test_throws_when_scene_is_active_and_missing_location(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        del mangled_scene['properties']['location']
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_is_missing_capture_date(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        del mangled_scene['properties']['acquiredDate']
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_is_missing_cloud_cover(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        del mangled_scene['properties']['cloudCover']
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_is_missing_geometry(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        del mangled_scene['geometry']
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_is_missing_resolution(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        del mangled_scene['properties']['resolution']
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_is_missing_status(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        del mangled_scene['properties']['status']
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_has_invalid_capture_date(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        mangled_scene['properties']['acquiredDate'] = None
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_has_invalid_cloud_cover(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        mangled_scene['properties']['cloudCover'] = None
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_has_invalid_geometry(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        mangled_scene['geometry'] = None
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_has_invalid_resolution(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        mangled_scene['properties']['resolution'] = None
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_has_invalid_status(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        mangled_scene['properties']['status'] = None
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_has_invalid_tide(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        mangled_scene['properties']['CurrentTide'] = 'whee'
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_has_invalid_tide_min(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        mangled_scene['properties']['24hrMinTide'] = 'whee'
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_throws_when_scene_has_invalid_tide_max(self):
        mangled_scene = json.loads(RESPONSE_SCENE_ACTIVE)
        mangled_scene['properties']['24hrMaxTide'] = 'whee'
        self.mock_requests.get('/planet/planetscope/test-scene-id', json=mangled_scene)
        with self.assertRaises(scenes.ValidationError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')

    def test_saves_scene_to_database(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        scenes.get('planetscope:test-scene-id', 'test-planet-api-key')
        self.assertTrue(self._mockdb.executed)

    def test_gracefully_handles_database_errors(self):
        self.mock_requests.get('/planet/planetscope/test-scene-id', text=RESPONSE_SCENE_INACTIVE)
        self._mockdb.raise_on_execute()
        with self.assertRaises(DatabaseError):
            scenes.get('planetscope:test-scene-id', 'test-planet-api-key')


#
# Helpers
#

def create_scene(*, platform: str = 'planetscope') -> scenes.Scene:
    return scenes.Scene(
        scene_id=platform + ':test-scene-id',
        uri='test-uri',
        capture_date=datetime.utcnow(),
        cloud_cover=33,
        geometry={"type": "Polygon", "coordinates": [[[0, 0], [0, 30], [30, 30], [30, 0], [0, 0]]]},
        platform=platform,
        resolution=7,
        sensor_name='test-sensor-name',
        status=scenes.STATUS_INACTIVE,
        tide=0.5,
        tide_min=0.0,
        tide_max=1.0,
    )


#
# Fixtures
#

RESPONSE_SCENE_ACTIVE = """{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [
          115.78907135188213,
          26.67939763560932
        ],
        [
          115.78653934657243,
          26.905071315070465
        ],
        [
          116.01004245933433,
          26.90679345550323
        ],
        [
          115.95815780815747,
          26.680701401397425
        ],
        [
          115.78907135188213,
          26.67939763560932
        ]
      ]
    ]
  },
  "properties": {
    "24hrMaxTide": 1.0,
    "24hrMinTide": 0.0,
    "CurrentTide": 0.5,
    "acquiredDate": "2017-01-20T00:00:00Z",
    "cloudCover": 1.47,
    "fileFormat": "geotiff",
    "location": "test-location",
    "permissions": [
      "download"
    ],
    "resolution": 3.9791881719258697,
    "sensorName": "test-sensor-name",
    "status": "active",
    "type": "analytic"
  },
  "id": "test-scene-id",
  "bbox": [
    115.78653934657243,
    26.67939763560932,
    116.01004245933433,
    26.90679345550323
  ]
}"""

RESPONSE_SCENE_INACTIVE = """{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [
          115.78907135188213,
          26.67939763560932
        ],
        [
          115.78653934657243,
          26.905071315070465
        ],
        [
          116.01004245933433,
          26.90679345550323
        ],
        [
          115.95815780815747,
          26.680701401397425
        ],
        [
          115.78907135188213,
          26.67939763560932
        ]
      ]
    ]
  },
  "properties": {
    "24hrMaxTide": 1.0,
    "24hrMinTide": 0.0,
    "CurrentTide": 0.5,
    "acquiredDate": "2017-01-20T00:00:00Z",
    "cloudCover": 1.47,
    "fileFormat": "geotiff",
    "permissions": [
      "download"
    ],
    "resolution": 3.9791881719258697,
    "sensorName": "test-sensor-name",
    "status": "inactive",
    "type": "analytic"
  },
  "id": "test-scene-id",
  "bbox": [
    115.78653934657243,
    26.67939763560932,
    116.01004245933433,
    26.90679345550323
  ]
}"""
