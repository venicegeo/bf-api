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

import unittest

import dateutil.parser
import requests_mock as rm

from bfapi.service import scenes as service


@rm.Mocker()
class SceneFetchTest(unittest.TestCase):
    def test_calls_correct_url(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        service.fetch('landsat:LC80110632016220LGN00')
        self.assertEqual(m.request_history[0].url,
                         'https://pzsvc-image-catalog.localhost/image/landsat:LC80110632016220LGN00')

    def test_fetches_scenes(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        scene = service.fetch('landsat:LC80110632016220LGN00')
        self.assertIsInstance(scene, service.Scene)

    def test_yields_correct_capture_date(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        scene = service.fetch('landsat:LC80110632016220LGN00')
        self.assertEqual(scene.capture_date, dateutil.parser.parse('2016-08-07T15:33:42.572449+00:00'))

    def test_yields_correct_bands(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        scene = service.fetch('landsat:LC80110632016220LGN00')
        self.assertSetEqual(set(scene.bands.keys()),
                            {'blue', 'cirrus', 'coastal', 'green', 'nir', 'panchromatic', 'red', 'swir1', 'swir2',
                             'tirs1', 'tirs2'})

    def test_yields_correct_cloud_cover(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        scene = service.fetch('landsat:LC80110632016220LGN00')
        self.assertEqual(scene.cloud_cover, 1.47)

    def test_yields_correct_id(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        scene = service.fetch('landsat:LC80110632016220LGN00')
        self.assertEqual(scene.id, 'landsat:LC80110632016220LGN00')

    def test_yields_correct_geometry(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        scene = service.fetch('landsat:LC80110632016220LGN00')
        self.assertIsInstance(scene.geometry, dict)
        self.assertIsInstance(scene.geometry.get('coordinates'), list)
        self.assertEqual(scene.geometry.get('coordinates'), [
            [[-81.5725334896228, -3.29632263428811], [-79.934112104967, -3.64597257671337],
             [-80.3035877737851, -5.38806769101045], [-81.9453446162527, -5.03306405829352],
             [-81.5725334896228, -3.29632263428811]]])

    def test_yields_correct_resolution(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        scene = service.fetch('landsat:LC80110632016220LGN00')
        self.assertEqual(scene.resolution, 30)

    def test_yields_correct_sensor_name(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        scene = service.fetch('landsat:LC80110632016220LGN00')
        self.assertEqual(scene.sensor_name, 'Landsat8')

    def test_yields_correct_uri(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', json=_generate_scene())
        scene = service.fetch('landsat:LC80110632016220LGN00')
        self.assertEqual(scene.uri, 'https://pzsvc-image-catalog.localhost/image/landsat:LC80110632016220LGN00')

    def test_gracefully_handles_errors(self, m: rm.Mocker):
        m.get('/image/landsat:LC80110632016220LGN00', status_code=400,
              text='Unable to retrieve metadata for landsat:LC80110632016220LGN00: lorem ipsum')
        with self.assertRaises(service.FetchError):
            service.fetch('landsat:LC80110632016220LGN00')


#
# Helpers
#

def _generate_scene():
    return {
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
