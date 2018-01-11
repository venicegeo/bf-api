SELECT j.job_id, j.algorithm_name, j.algorithm_version, j.created_by, j.created_on, j.name, j.scene_id, j.status, j.tide, j.tide_min_24h, j.tide_max_24h, j.compute_mask,
       e.error_message, e.execution_step,
       ST_AsGeoJSON(s.geometry) AS geometry, s.sensor_name, s.captured_on
  FROM __beachfront__job j
       LEFT OUTER JOIN __beachfront__job_user u ON (u.job_id = j.job_id)
       LEFT OUTER JOIN __beachfront__job_error e ON (e.job_id = j.job_id)
       LEFT OUTER JOIN __beachfront__scene s ON (s.scene_id = j.scene_id)
  WHERE u.user_id = ?
ORDER BY created_on ASC