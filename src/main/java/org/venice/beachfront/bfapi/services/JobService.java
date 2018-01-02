package org.venice.beachfront.bfapi.services;

import java.util.List;

import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;

import com.fasterxml.jackson.databind.JsonNode;

public interface JobService {
	public Job createJob(String jobName, 
			String creatorUserId,
			String sceneId,
			String algorithmId,
			String planetApiKey,
			JsonNode extras);
	public List<Job> getJobs();
	public Job getJob(String jobId);
	public Confirmation deleteJob(Job job);
	
	public List<JobStatus> searchJobsByInputs(String algorithmId, String sceneId);
}
