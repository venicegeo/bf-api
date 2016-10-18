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

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS job_error;
DROP TABLE IF EXISTS job_user;
DROP TABLE IF EXISTS job;
DROP TABLE IF EXISTS scene;

CREATE TABLE scene (
    scene_id          VARCHAR(32)    PRIMARY KEY,
    captured_on       TIMESTAMP      NOT NULL,
    cloud_cover       FLOAT          NOT NULL,
    geometry          VARCHAR(4000)  NOT NULL,
    resolution        INTEGER        NOT NULL,
    sensor_name       VARCHAR(32)    NOT NULL,
    catalog_uri       VARCHAR(255)   NOT NULL
);

CREATE TABLE job (
    job_id            VARCHAR(32)    PRIMARY KEY,
    algorithm_name    VARCHAR(100)   NOT NULL,
    algorithm_version VARCHAR(12)    NOT NULL,
    created_by        VARCHAR(64)    NOT NULL,
    created_on        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    detections_id     VARCHAR(32),
    name              VARCHAR(100)   NOT NULL,
    scene_id          VARCHAR(32)    NOT NULL,
    status            VARCHAR(16)    NOT NULL,

    FOREIGN KEY (scene_id) REFERENCES scene(scene_id)
);

CREATE TABLE job_user (
    job_id            VARCHAR(32),  -- on create, automatically fill this
    user_id           VARCHAR(64),

    PRIMARY KEY (job_id, user_id),
    FOREIGN KEY (job_id) REFERENCES job(job_id)
);

CREATE TABLE job_error (
    job_id            VARCHAR(32),
    error_message     VARCHAR(64),
    execution_step    VARCHAR(64),  -- e.g., 'fetch', 'compute', 'deployment', 'async'

    FOREIGN KEY (job_id) REFERENCES job(job_id)
);
