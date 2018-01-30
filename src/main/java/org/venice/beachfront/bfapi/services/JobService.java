package org.venice.beachfront.bfapi.services;

import java.util.List;

import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;

import com.fasterxml.jackson.databind.JsonNode;

@Service
public class JobService {
	public Job createJob(String jobName, String creatorUserId, String sceneId, String algorithmId, String planetApiKey, Boolean computeMask,
			JsonNode extras) {
		return null; // TODO
	}

	public List<Job> getJobs() {
		return null; // TODO
	}

	public Job getJob(String jobId) {
		return null; // TODO
	}

	public Confirmation deleteJob(Job job) {
		return null; // TODO
	}

	public List<JobStatus> searchJobsByInputs(String algorithmId, String sceneId) {
		return null; // TODO
	}
}
