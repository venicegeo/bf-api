package org.venice.beachfront.bfapi.database.dao;

import java.util.List;
import javax.transaction.Transactional;

import org.springframework.data.repository.CrudRepository;
import org.venice.beachfront.bfapi.model.Detection;

@Transactional
public interface DetectionDao extends CrudRepository<Detection, Long> {
	Detection findByJob_JobIdAndFeatureId(String jobId, String featureId);

    List<Detection> findByJob_JobId(String jobId);

    List<Detection> findByFeatureId(String featureId);
}
