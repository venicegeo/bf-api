-- Copyright 2016, RadiantBlue Technologies, Inc.
--
-- Licensed under the Apache License, Version 2.0 (the "License"); you may not
-- use this file except in compliance with the License. You may obtain a copy
-- of the License at
--
-- http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
-- WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
-- License for the specific language governing permissions and limitations
-- under the License.

-- SQL Dialect: PostgreSQL + PostGIS

DELETE FROM __beachfront__job_user;
DELETE FROM __beachfront__job_error;
DELETE FROM __beachfront__job;
DELETE FROM __beachfront__scene;

INSERT INTO __beachfront__scene (scene_id, captured_on, cloud_cover, geometry, resolution, sensor_name, catalog_uri)
VALUES ('landsat:LC80070692016272LGN00', '2016-09-28T15:11:34.822768+00:00', 50.83, ST_GeomFromGeoJSON('{"type": "Polygon", "coordinates": [[[-77.281626203942, -11.968484212527], [-75.6109126167935, -12.3202750912018], [-75.9822885062088, -14.0602902160846], [-77.6701681325985, -13.701734900813], [-77.281626203942, -11.968484212527]]]}'), 30, 'Landsat8', 'https://pzsvc-image-catalog.geointservices.io/image/landsat:LC80070692016272LGN00'),
       ('landsat:LC80070682016272LGN00', '2016-09-28T15:11:10.885134+00:00', 56.37, ST_GeomFromGeoJSON('{"type": "Polygon", "coordinates": [[[-76.9554504682419, -10.5245344623787], [-75.2951331214004, -10.8760956328548], [-75.674853061268, -12.6139156283324], [-77.3463760328369, -12.2572036608123], [-76.9554504682419, -10.5245344623787]]]}'), 30, 'Landsat8', 'https://pzsvc-image-catalog.geointservices.io/image/landsat:LC80070682016272LGN00'),
       ('landsat:LC80070672016272LGN00', '2016-09-28T15:10:46.960208+00:00', 78.06, ST_GeomFromGeoJSON('{"coordinates": [[[-76.6405646284069, -9.07955489140534], [-74.9847423418657, -9.43056641296655], [-75.3591732922923, -11.1704039866521], [-77.0214904475732, -10.8148117455668], [-76.6405646284069, -9.07955489140534]]], "type": "Polygon"}'), 30, 'Landsat8', 'https://pzsvc-image-catalog.geointservices.io/image/landsat:LC80070672016272LGN00'),
       ('landsat:LC80070662016272LGN00', '2016-09-28T15:10:23.031047+00:00', 81.11, ST_GeomFromGeoJSON('{"coordinates": [[[-76.3278188415546, -7.63348611630521], [-74.6761005274902, -7.98437953622967], [-75.048182808865, -9.72497154017745], [-76.7022655591329, -9.37003642172753], [-76.3278188415546, -7.63348611630521]]], "type": "Polygon"}'), 30, 'Landsat8', 'https://pzsvc-image-catalog.geointservices.io/image/landsat:LC80070662016272LGN00'),
       ('landsat:LC80070652016272LGN00', '2016-09-28T15:09:59.106121+00:00', 76.58, ST_GeomFromGeoJSON('{"coordinates": [[[-76.014989631339, -6.18810138577879], [-74.3686132999089, -6.53822024230797], [-74.7396098770223, -8.27939504902005], [-76.3907726033767, -7.92357053058024], [-76.014989631339, -6.18810138577879]]], "type": "Polygon"}'), 30, 'Landsat8', 'https://pzsvc-image-catalog.geointservices.io/image/landsat:LC80070652016272LGN00');

INSERT INTO __beachfront__job (job_id, algorithm_name, algorithm_version, created_by, detections_id, name, scene_id, status)
VALUES ('JOB_FIXTURE_01', 'NDWI', '13', 'baziledd', 'D0001', 'FIXTURE_ONE', 'landsat:LC80070682016272LGN00', 'Success'),
       ('JOB_FIXTURE_02', 'NDWI', '13', 'baziledd', NULL, 'FIXTURE_TWO', 'landsat:LC80070682016272LGN00', 'Running'),
       ('JOB_FIXTURE_03', 'NDWI', '13', 'baziledd', 'D0002', 'FIXTURE_THREE', 'landsat:LC80070672016272LGN00', 'Success'),
       ('JOB_FIXTURE_04', 'NDWI', '13', 'baziledd', NULL, 'FIXTURE_FOUR', 'landsat:LC80070662016272LGN00', 'Error'),
       ('JOB_FIXTURE_05', 'NDWI', '13', 'baziledd', NULL, 'FIXTURE_FIVE', 'landsat:LC80070652016272LGN00', 'Error'),
       ('JOB_FIXTURE_06', 'NDWI', '13', 'baziledd', NULL, 'FIXTURE_SIX', 'landsat:LC80070652016272LGN00', 'Error');

INSERT INTO __beachfront__job_user (job_id, user_id)
VALUES ('JOB_FIXTURE_01', 'baziledd');

INSERT INTO __beachfront__job_error (job_id, error_message, execution_step)
VALUES ('JOB_FIXTURE_04', 'Could not fetch GeoTIFF', 'EXTERNAL:FETCH_GEOTIFF'),
       ('JOB_FIXTURE_05', 'Piazza is down', 'PIAZZA:UPLOAD_VECTOR'),
       ('JOB_FIXTURE_06', 'User credentials rejected', 'PIAZZA:UPLOAD_VECTOR');
