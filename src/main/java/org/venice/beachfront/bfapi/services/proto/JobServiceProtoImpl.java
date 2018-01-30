package org.venice.beachfront.bfapi.services.proto;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.joda.time.DateTime;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;
import org.venice.beachfront.bfapi.services.JobService;

import com.fasterxml.jackson.databind.JsonNode;

@Profile("prototype")
@Service
public class JobServiceProtoImpl implements JobService {

	@Override
	public Job createJob(String jobName, 
			String creatorUserId,
			String sceneId,
			String algorithmId,
			String planetApiKey,
			JsonNode extras) {
		return new Job(
				"job-id-123", 
				jobName, 
				"in-progress", 
				creatorUserId, 
				DateTime.now(), 
				"algo name", 
				"algo version 1.0", 
				null, //geometry 
				"RE-3", 
				DateTime.now().minusDays(1), 
				sceneId,
				0,
				0,
				0,
				extras, 
				planetApiKey);
	}

	@Override
	public List<Job> getJobs() {
		Job job = this.createJob("job-name", 
				"user-id-123",
				"SCENE-ID-123",
				"ndwi-id-1.0", 
				"planet-key-abc-123", 
				null);
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
				0,
				0,
				0,
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

	@Override
	public List<JobStatus> searchJobsByInputs(String algorithmId, String sceneId) {
		return Collections.singletonList(new JobStatus("job-id-123", "in-progress"));
	}

}
