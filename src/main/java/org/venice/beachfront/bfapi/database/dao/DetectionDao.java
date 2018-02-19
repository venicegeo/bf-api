package org.venice.beachfront.bfapi.database.dao;

import javax.transaction.Transactional;

import org.springframework.data.repository.CrudRepository;
import org.venice.beachfront.bfapi.model.Detection;
import org.venice.beachfront.bfapi.model.DetectionPK;

@Transactional
public interface DetectionDao extends CrudRepository<Detection, DetectionPK> {
	Detection findByDetectionPK_Job_JobIdAndDetectionPK_FeatureId(String jobId, int featureId);

	Detection findByDetectionPK_Job_JobId(String jobId);
}
