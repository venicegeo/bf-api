package org.venice.beachfront.bfapi.database.dao;

import java.util.List;
import javax.transaction.Transactional;

import org.springframework.data.repository.CrudRepository;
import org.venice.beachfront.bfapi.model.Detection;
import org.venice.beachfront.bfapi.model.DetectionPK;

@Transactional
public interface DetectionDao extends CrudRepository<Detection, DetectionPK> {
	Detection findByJob_JobIdAndFeatureId(String jobId, int featureId);

    List<Detection> findByJob_JobId(String jobId);

    List<Detection> findByFeatureId(int featureId);
}
