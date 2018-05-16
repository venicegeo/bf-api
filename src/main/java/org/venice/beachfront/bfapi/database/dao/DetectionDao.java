/**
 * Copyright 2018, Radiant Solutions, Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
package org.venice.beachfront.bfapi.database.dao;

import javax.transaction.Transactional;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;
import org.venice.beachfront.bfapi.model.Detection;
import org.venice.beachfront.bfapi.model.DetectionPK;

@Transactional
public interface DetectionDao extends CrudRepository<Detection, DetectionPK> {
	Detection findByDetectionPK_Job_JobIdAndDetectionPK_FeatureId(String jobId, int featureId);

	Detection findByDetectionPK_Job_JobId(String jobId);

	@Query(value = "SELECT CAST(to_json(fc) AS text) AS \"feature_collection\" FROM( SELECT 'FeatureCollection' AS \"type\", array_agg(geomQuery) AS \"features\" FROM (SELECT  to_json(p) AS \"properties\", CAST(ST_AsGeoJSON((p_geom).geom) AS json) as \"geometry\", 'Feature' as \"type\", concat_ws('#', d.job_id, (p_geom.path[1])) AS \"id\" FROM  __beachfront__detection as d LEFT JOIN lateral st_dump(d.geometry) as p_geom ON TRUE INNER JOIN __beachfront__provenance AS p ON (p.job_id = d.job_id) WHERE d.job_id = ?1) as geomQuery ) as fc", nativeQuery = true)
	byte[] findFullDetectionGeoJson(String jobId);
}
