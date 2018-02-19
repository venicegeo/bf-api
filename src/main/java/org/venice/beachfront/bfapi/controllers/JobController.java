/**
 * Copyright 2016, RadiantBlue Technologies, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
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
import org.venice.beachfront.bfapi.model.exception.UserException;
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
public class JobController {
	@Autowired
	private JobService jobService;
	@Autowired
	private UserProfileService userProfileService;

	@Autowired
	public JobController(JobService jobService, UserProfileService userProfileService) {
		this.jobService = jobService;
		this.userProfileService = userProfileService;
	}

	@RequestMapping(path = "/job", method = RequestMethod.POST, consumes = { "application/json" }, produces = { "application/json" })
	@ResponseBody
	public Job createJob(@RequestBody CreateJobBody body) throws UserException {
		UserProfile currentUser = userProfileService.getCurrentUserProfile();
		return jobService.createJob(body.jobName, currentUser.getUserId(), body.algorithmId, body.sceneId, body.planetApiKey,
				body.computeMask, body.extras);
	}

	@RequestMapping(path = "/job", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public List<Job> listJobs() {
		UserProfile currentUser = userProfileService.getCurrentUserProfile();
		return jobService.getJobsForUser(currentUser.getUserId());
	}

	@RequestMapping(path = "/job/{id}", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public Job getJobById(@PathVariable("id") String id) {
		Job job = jobService.getJob(id);
		if (job == null) {
			throw new JobNotFoundException();
		}
		return job;
	}

	@RequestMapping(path = "/job/{id}", method = RequestMethod.DELETE, produces = { "application/json" })
	@ResponseBody
	public Confirmation deleteJob(@PathVariable("id") String id) {
		Job job = jobService.getJob(id);
		return jobService.forgetJob(job.getJobId(), userProfileService.getCurrentUserProfile().getUserId());
	}

	private static class CreateJobBody {
		public final String jobName;
		public final String algorithmId;
		public final String sceneId;
		public final String planetApiKey;
		public final Boolean computeMask;
		public final JsonNode extras;

		@JsonCreator
		public CreateJobBody(@JsonProperty(value = "name", required = true) String jobName,
				@JsonProperty(value = "algorithm_id", required = true) String algorithmId,
				@JsonProperty(value = "scene_id", required = true) String sceneId,
				@JsonProperty(value = "planet_api_key", required = true) String planetApiKey,
				@JsonProperty(value = "compute_mask", required = true) Boolean computeMask,
				@JsonProperty(value = "extras") JsonNode extras) {
			this.jobName = jobName;
			this.algorithmId = algorithmId;
			this.sceneId = sceneId;
			this.planetApiKey = planetApiKey;
			this.computeMask = computeMask;
			this.extras = extras;
		}
	}

	@RequestMapping(path = "/job/{id}.geojson", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public byte[] downloadJobGeoJson(@PathVariable("id") String id) throws UserException {
		return jobService.getDetectionGeoJson(id);
	}

	@RequestMapping(path = "/job/{id}.gpkg", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public byte[] downloadJobGeoPackage(@PathVariable("id") String id) {
		return null;
		// TODO
	}

	@ResponseStatus(value = HttpStatus.NOT_FOUND)
	private static class JobNotFoundException extends RuntimeException {
		private static final long serialVersionUID = 1L;
	}

	@RequestMapping(path = "/job/searchByInputs", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public List<JobStatus> searchJobsByInputs(@RequestParam(value = "algorithm_id", required = true) String algorithmId,
			@RequestParam(value = "scene_id", required = true) String sceneId) {
		return jobService.searchJobsByInputs(algorithmId, sceneId);
	}
}
