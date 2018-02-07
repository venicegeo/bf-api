package org.venice.beachfront.bfapi.services;

import java.util.List;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;

import com.fasterxml.jackson.databind.JsonNode;

@Service
public class JobService {
	@Autowired
	private JobDao jobDao;

	public Job createJob(String jobName, String creatorUserId, String sceneId, String algorithmId, String planetApiKey, Boolean computeMask,
			JsonNode extras) {
		Job job = new Job(
				"XXX",
				jobName,
				"Success",
				creatorUserId,
				DateTime.now(),
				algorithmId,
				"algName",
				"algVersion",
				sceneId,
				0.0,
				0.0,
				0.0,
				extras,
				computeMask);
		return jobDao.save(job); // TODO
	}

	public List<Job> getJobs() {
		return null; // TODO
	}

	public Job getJob(String jobId) {
		return jobDao.findByJobId(jobId);
	}

	public Confirmation deleteJob(Job job) {
		return null; // TODO
	}

	public List<JobStatus> searchJobsByInputs(String algorithmId, String sceneId) {
		return null; // TODO
	}
}
