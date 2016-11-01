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

CREATE TABLE __beachfront__scene (
    scene_id          VARCHAR(64)    PRIMARY KEY,
    captured_on       TIMESTAMP      NOT NULL,
    cloud_cover       FLOAT          NOT NULL,
    geometry          GEOMETRY       NOT NULL,
    resolution        INTEGER        NOT NULL,
    sensor_name       VARCHAR(64)    NOT NULL,
    catalog_uri       VARCHAR(255)   NOT NULL
);

CREATE TABLE __beachfront__job (
    job_id            VARCHAR(64)    PRIMARY KEY,
    algorithm_id      VARCHAR(64)    NOT NULL,
    algorithm_name    VARCHAR(100)   NOT NULL,
    algorithm_version VARCHAR(12)    NOT NULL,
    created_by        VARCHAR(64)    NOT NULL,
    created_on        TIMESTAMP      NOT NULL    DEFAULT CURRENT_TIMESTAMP,
    detections_id     VARCHAR(64),  -- TODO -- is this still needed?
    name              VARCHAR(100)   NOT NULL,
    scene_id          VARCHAR(64)    NOT NULL,
    status            VARCHAR(16)    NOT NULL,

    FOREIGN KEY (scene_id) REFERENCES __beachfront__scene(scene_id)
);

CREATE TABLE __beachfront__detection (
    job_id            VARCHAR(64),
    feature_id        INT,
    geometry          GEOMETRY       NOT NULL,

    PRIMARY KEY (job_id, feature_id),
    FOREIGN KEY (job_id) REFERENCES __beachfront__job(job_id)
);

CREATE TABLE __beachfront__job_user (
    job_id            VARCHAR(64),
    user_id           VARCHAR(64),

    PRIMARY KEY (job_id, user_id),
    FOREIGN KEY (job_id) REFERENCES __beachfront__job(job_id)
);

CREATE TABLE __beachfront__job_error (
    job_id            VARCHAR(64)    PRIMARY KEY,
    error_message     VARCHAR(64)    NOT NULL,
    execution_step    VARCHAR(64)    NOT NULL,  -- e.g., 'fetch', 'compute', 'deployment', 'async'

    FOREIGN KEY (job_id) REFERENCES __beachfront__job(job_id)
);

CREATE TABLE __beachfront__productline (
-- TODO -- add check constraint for start_on/stop_on
    productline_id    VARCHAR(64)    PRIMARY KEY,
    algorithm_id      VARCHAR(64)    NOT NULL,  -- Pz Service ID
    algorithm_name    VARCHAR(100)   NOT NULL,
    bbox              GEOMETRY,
    category          VARCHAR(64),
    compute_mask      GEOMETRY,
    created_by        VARCHAR(64)    NOT NULL,
    created_on        TIMESTAMP      NOT NULL    DEFAULT CURRENT_TIMESTAMP,
    max_cloud_cover   INTEGER        NOT NULL,
    name              VARCHAR(100)   NOT NULL,
    owned_by          VARCHAR(64)    NOT NULL,
    spatial_filter_id VARCHAR(64),
    start_on          DATE           NOT NULL,
    stop_on           DATE
);

CREATE TABLE __beachfront__productline_job (
    productline_id    VARCHAR(64),
    job_id            VARCHAR(64),

    PRIMARY KEY (productline_id, job_id),
    FOREIGN KEY (productline_id) REFERENCES __beachfront__productline(productline_id),
    FOREIGN KEY (job_id) REFERENCES __beachfront__job(job_id)
);
