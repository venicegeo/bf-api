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

INSERT INTO __beachfront__productline (productline_id, algorithm_id, algorithm_name, bbox, category, compute_mask, created_by, max_cloud_cover, name, owned_by, spatial_filter_id, start_on, stop_on)
VALUES ('PRODUCTLINE_FIXTURE_01', 'test-algorithm-id', 'NDWI', ST_MakeEnvelope(49.5732721406616, -18.3921153881594, 51.6869513918079, -16.2990911367903), NULL, NULL, 'test-username', 10, 'Fixture: Active', 'test-username', NULL, CURRENT_DATE - 1, CURRENT_DATE + 10),
       ('PRODUCTLINE_FIXTURE_02', 'test-algorithm-id', 'NDWI', ST_MakeEnvelope(49.5732721406616, -18.3921153881594, 51.6869513918079, -16.2990911367903), NULL, NULL, 'test-username', 10, 'Fixture: Active (Forever)', 'test-username', NULL, CURRENT_DATE, NULL),
       ('PRODUCTLINE_FIXTURE_03', 'test-algorithm-id', 'NDWI', ST_MakeEnvelope(49.5732721406616, -18.3921153881594, 51.6869513918079, -16.2990911367903), NULL, NULL, 'test-username', 10, 'Fixture: Expired', 'test-username', NULL, CURRENT_DATE - 10, CURRENT_DATE - 1),
       ('PRODUCTLINE_FIXTURE_04', 'test-algorithm-id', 'NDWI', ST_MakeEnvelope(49.5732721406616, -18.3921153881594, 51.6869513918079, -16.2990911367903), NULL, NULL, 'test-username', 10, 'Fixture: Not Yet Started', 'test-username', NULL, CURRENT_DATE + 5, NULL);
