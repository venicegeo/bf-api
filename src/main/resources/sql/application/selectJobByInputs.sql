SELECT job_id,
	CASE status
		WHEN 'Success' THEN 0
		WHEN 'Submitted' THEN 1
		WHEN 'Running' THEN 2
	END AS _sort_precedence
FROM __beachfront__job
WHERE algorithm_id = ?
	AND scene_id = ?
	AND status IN ('Submitted', 'Running', 'Success')
ORDER BY _sort_precedence ASC