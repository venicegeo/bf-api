SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.name, j.scene_id, j.status, j.tide, j.tide_min_24h, j.tide_max_24h, j.compute_mask
       ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name, s.captured_on
  FROM __beachfront__job j
       LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
 WHERE j.algorithm_id = ?
   AND j.algorithm_version = ?
   AND j.scene_id = ?
   AND j.compute_mask = ?
   AND j.status IN ('Submitted', 'Running', 'Success')
ORDER BY created_on DESC