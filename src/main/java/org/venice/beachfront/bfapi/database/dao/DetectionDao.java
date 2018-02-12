package org.venice.beachfront.bfapi.database.dao;

import java.util.List;
import javax.transaction.Transactional;

import org.springframework.data.repository.CrudRepository;
import org.venice.beachfront.bfapi.model.Detection;
import org.venice.beachfront.bfapi.model.DetectionPK;

@Transactional
public interface DetectionDao extends CrudRepository<Detection, DetectionPK> {
	Detection findByDetectionPK_Job_JobIdAndDetectionPK_FeatureId(String jobId, int featureId);

    List<Detection> findByDetectionPK_Job_JobId(String jobId);

    List<Detection> findByDetectionPK_FeatureId(int featureId);
}
