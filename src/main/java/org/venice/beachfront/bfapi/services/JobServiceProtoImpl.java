package org.venice.beachfront.bfapi.services;

import java.util.ArrayList;
import java.util.List;

import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;

import com.fasterxml.jackson.databind.JsonNode;

public class JobServiceProtoImpl implements JobService {

	@Override
	public Job createJob(String jobName, 
			String creatorUserId,
			String algorithmName, 
			String algorithmVersion,
			JsonNode geometry,
			String sceneSensorName,
			DateTime sceneCollectionTime,
			String sceneId,
			JsonNode extras,
			String planetApiKey) {
		return new Job(
				"job-id-123", 
				jobName, 
				"in-progress", 
				creatorUserId, 
				DateTime.now(), 
				algorithmName, 
				algorithmVersion, 
				geometry, 
				sceneSensorName, 
				sceneCollectionTime, 
				sceneId, 
				extras, 
				planetApiKey);
	}

	@Override
	public List<Job> getJobs() {
		Job job = this.createJob("job-name", 
				"user-id-123",
				"ndwi", 
				"1.0",
				null, // JsonNode 
				"Sentinel-2",
				DateTime.now().minusDays(7),
				"SCENE-ID-123",
				null, // JsonNode
				"planet-key-abc-123");
		List<Job> jobs = new ArrayList<Job>();
		jobs.add(job);
		return jobs;
	}

	@Override
	public Job getJob(String jobId) {
		return new Job(
				jobId, 
				"Job Name Foo Bar", 
				"in-progress", 
				"created-by-456", 
				DateTime.now(), 
				"ndwi", 
				"1.0", 
				null, 
				"Sentinel-2", 
				DateTime.now(), 
				"S2-ABC-1234", 
				null, 
				"PL_API_1234567");
	}

	@Override
	public Confirmation deleteJob(Job job) {
		if (job.getJobId().equals("doNotDelete")) {
			return new Confirmation(job.getJobId(), false);
		}
		return new Confirmation(job.getJobId(), true);
	}

}
