package org.venice.beachfront.bfapi.controllers;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.JobService;
import org.venice.beachfront.bfapi.services.UserProfileService;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * Main controller class for the Job CRUD endpoints.
 * 
 * @version 1.0
 */
@Controller
public class JobCrudController {
	private JobService jobService;
	private UserProfileService userProfileService;
	
	@Autowired
	public JobCrudController(JobService jobService, UserProfileService userProfileService) {
		this.jobService = jobService;
		this.userProfileService = userProfileService;
	}
	
	@RequestMapping(
			path="/job",
			method=RequestMethod.POST,
			consumes={"application/json"},
			produces={"application/json"})
	@ResponseBody
	public Job createJob(@RequestBody CreateJobBody body) {
		UserProfile currentUser = this.userProfileService.getCurrentUserProfile();
		return this.jobService.createJob(
				body.jobName,
				currentUser.getId(),
				body.algorithmId,
				body.sceneId,
				body.planetApiKey,
				body.extras
				);
	}
	
	@RequestMapping(
	        path="/job",
	        method=RequestMethod.GET,
	        produces={"application/json"})
	@ResponseBody
	public List<Job> listJobs() {
		return this.jobService.getJobs();
	}
	
	@RequestMapping(
			path="/job/{id}",
			method=RequestMethod.GET,
			produces={"application/json"})
	@ResponseBody
	public Job getJobById(@PathVariable("id") String id) {
		Job job = this.jobService.getJob(id);
		if (job == null) {
			throw new JobNotFoundException();
		}
		return job;
	}
	
	@RequestMapping(
			path="/job/{id}",
			method=RequestMethod.DELETE,
			produces={"application/json"})
	@ResponseBody
	public Confirmation deleteJob(@PathVariable("id") String id) {
		Job job = this.jobService.getJob(id);
		return this.jobService.deleteJob(job);
	}

	private static class CreateJobBody {
		public final String jobName;
		public final String algorithmId;
		public final String sceneId;
		public final String planetApiKey;
		public final JsonNode extras;

		@JsonCreator
		public CreateJobBody(
				@JsonProperty(value="name", required=true) String jobName,
				@JsonProperty(value="algorithm_id", required=true) String algorithmId,
				@JsonProperty(value="scene_id", required=true) String sceneId,
				@JsonProperty(value="planet_api_key", required=true) String planetApiKey,
				@JsonProperty(value="extras") JsonNode extras) {
			this.jobName = jobName;
			this.algorithmId = algorithmId;
			this.sceneId = sceneId;
			this.planetApiKey = planetApiKey;
			this.extras = extras;
		}	
	}
	
	@ResponseStatus(value=HttpStatus.NOT_FOUND)
	private static class JobNotFoundException extends RuntimeException {
		private static final long serialVersionUID = 1L;
	}
	
	@RequestMapping(path="/job/searchByInputs",
			method=RequestMethod.GET,
			produces={"application/json"})
	@ResponseBody
	public List<JobStatus> searchJobsByInputs(
			@RequestParam(value="algorithm_id", required=true) String algorithmId,
			@RequestParam(value="scene_id", required=true) String sceneId) {
		return this.jobService.searchJobsByInputs(algorithmId, sceneId);
	}
}
