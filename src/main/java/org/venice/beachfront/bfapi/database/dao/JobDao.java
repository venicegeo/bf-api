package org.venice.beachfront.bfapi.database.dao;

import java.util.List;
import javax.transaction.Transactional;

import org.springframework.data.repository.CrudRepository;
import org.venice.beachfront.bfapi.model.Job;

@Transactional
public interface JobDao extends CrudRepository<Job, Long> {
	Job findByJobId(String jobId);

	List<Job> findByAlgorithmIdAndSceneId(String algorithmId, String sceneId);

	List<Job> findBySceneIdAndAlgorithmIdAndAlgorithmVersionAndComputeMaskAndStatus(String sceneId, String algorithmId,
			String algorithmVersion, Boolean computeMask, String status);
}
