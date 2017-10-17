package org.venice.beachfront.bfapi.controllers;

import java.util.List;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.services.JobService;

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
	
	@Autowired
	public JobCrudController(JobService jobService) {
		this.jobService = jobService;
	}
	
	@RequestMapping(
			path="/job",
			method=RequestMethod.POST,
			consumes={"application/json"},
			produces={"application/json"})
	@ResponseBody
	public Job createJob(@RequestBody CreateJobBody body) {
		String currentUserId = "blah blah user id";
		return this.jobService.createJob(
				body.jobName,
				currentUserId,
				body.algorithmName,
				body.algorithmVersion,
				body.geometry,
				body.sceneSensorName,
				body.sceneCollectionTime,
				body.sceneId,
				body.extras,
				body.planetApiKey);
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
		return this.jobService.getJob(id);
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
		public String jobName;
		public String algorithmName;
		public String algorithmVersion;
		public JsonNode geometry;
		public String sceneSensorName;
		public DateTime sceneCollectionTime;
		public String sceneId;
		public JsonNode extras;
		public String planetApiKey;

		@JsonCreator
		public CreateJobBody(
				@JsonProperty(value="jobName", required=true) String jobName,
				@JsonProperty(value="algorithmName", required=true) String algorithmName,
				@JsonProperty(value="algorithmVersion", required=true) String algorithmVersion,
				@JsonProperty(value="geometry", required=true) JsonNode geometry ,
				@JsonProperty(value="sceneSensorName", required=true) String sceneSensorName,
				@JsonProperty(value="sceneCollectionTime", required=true) DateTime sceneCollectionTime,
				@JsonProperty(value="sceneId", required=true) String sceneId,
				@JsonProperty(value="extras") JsonNode extras,
				@JsonProperty(value="planetApiKey", required=true) String planetApiKey) {
			this.jobName = jobName;
			this.algorithmName = algorithmName;
			this.algorithmVersion = algorithmVersion;
			this.geometry = geometry;
			this.sceneSensorName = sceneSensorName;
			this.sceneCollectionTime = sceneCollectionTime;
			this.sceneId = sceneId;
			this.extras = extras;
			this.planetApiKey = planetApiKey;
		}
		
	}
}
