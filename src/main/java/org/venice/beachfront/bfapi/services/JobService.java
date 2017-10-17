package org.venice.beachfront.bfapi.services;

import java.util.List;

import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;

import com.fasterxml.jackson.databind.JsonNode;

public interface JobService {
	public Job createJob(String jobName, 
			String creatorUserId,
			String algorithmName, 
			String algorithmVersion,
			JsonNode geometry,
			String sceneSensorName,
			DateTime sceneCollectionTime,
			String sceneId,
			JsonNode extras,
			String planetApiKey);
	public List<Job> getJobs();
	public Job getJob(String jobId);
	public Confirmation deleteJob(Job job);
}
