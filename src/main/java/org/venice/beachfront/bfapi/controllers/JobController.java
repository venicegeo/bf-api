/**
 * Copyright 2018, Radiant Solutions, Inc.
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
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
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

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;

/**
 * Main controller class for the Job CRUD endpoints.
 * 
 * @version 1.0
 */
@Controller
@Api(value = "Job")
public class JobController {
	@Autowired
	private JobService jobService;
	@Autowired
	private UserProfileService userProfileService;

	@RequestMapping(path = "/job", method = RequestMethod.POST, consumes = { "application/json" }, produces = { "application/json" })
	@ResponseBody
	@ApiOperation(value = "Submit Job", notes = "Creates a new shoreline detection job request", tags = "Job")
	@ApiResponses(value = { @ApiResponse(code = 201, message = "The created Job information", response = Job.class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public ResponseEntity<JsonNode> createJob(@ApiParam(value = "Job request parameters", required = true) @RequestBody CreateJobBody body,
			Authentication authentication) throws UserException {
		UserProfile currentUser = userProfileService.getProfileFromAuthentication(authentication);
		Job createdJob = jobService.createJob(body.jobName, currentUser.getUserId(), body.sceneId, body.algorithmId, body.planetApiKey,
				body.computeMask, body.extras);
		JsonNode response = jobService.getJobGeoJson(createdJob);
		return new ResponseEntity<>(response, HttpStatus.CREATED);
	}

	@RequestMapping(path = "/job", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	@ApiOperation(value = "Get User Jobs", notes = "Retrieves all Jobs owned by the User", tags = "Job")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "The list of Jobs", response = JsonNode.class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public JsonNode listJobs(Authentication authentication) throws UserException {
		UserProfile currentUser = userProfileService.getProfileFromAuthentication(authentication);
		List<Job> jobs = jobService.getJobsForUser(currentUser.getUserId());
		return jobService.getJobsGeoJson(jobs);
	}

	@RequestMapping(path = "/job/{id}", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	@ApiOperation(value = "Get Job Information", notes = "Returns information on a specific Job", tags = "Job")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "The Job information", response = Job.class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 404, message = "Job not found", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public JsonNode getJobById(@ApiParam(value = "ID of the Job", required = true) @PathVariable("id") String id) throws UserException {
		Job job = jobService.getJob(id);
		if (job == null) {
			throw new UserException(String.format("Job %s not found.", id), HttpStatus.NOT_FOUND);
		}
		return jobService.getJobGeoJson(job);
	}

	@RequestMapping(path = "/job/{id}", method = RequestMethod.DELETE, produces = { "application/json" })
	@ResponseBody
	@ApiOperation(value = "Delete a Job", notes = "Removes the Job from the User table", tags = "Job")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "Deletion Confirmation", response = Confirmation.class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 404, message = "Job not found", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public Confirmation deleteJob(@ApiParam(value = "ID of the Job", required = true) @PathVariable("id") String id,
			Authentication authentication) throws UserException {
		UserProfile currentUser = userProfileService.getProfileFromAuthentication(authentication);
		Job job = jobService.getJob(id);
		if (job == null) {
			throw new UserException(String.format("Job %s not found.", id), HttpStatus.NOT_FOUND);
		}
		return jobService.forgetJob(job.getJobId(), currentUser.getUserId());
	}

	@RequestMapping(path = "/job", method = RequestMethod.DELETE, produces = { "application/json" })
	@ResponseBody
	@ApiOperation(value = "Delete all Jobs", notes = "Removes all Jobs from the User's table", tags = "Job")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "Deletion Confirmation", response = Confirmation.class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public Confirmation deleteAllJobs(
			@ApiParam(value = "Confirmation boolean", required = true) @RequestParam(value = "confirm", required = false) Boolean confirm,
			Authentication authentication) throws UserException {
		UserProfile currentUser = userProfileService.getProfileFromAuthentication(authentication);
		// Check the confirm flag in the request. This might prevent an accidental deletion.
		if ((confirm != null) && (confirm.booleanValue())) {
			return jobService.forgetAllJobs(currentUser.getUserId());
		} else {
			// Confirm flag must be set
			return new Confirmation("delete jobs", false);
		}
	}

	public static class CreateJobBody {
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
	@ApiOperation(value = "Download Detection GeoJSON", notes = "Downloads GeoJSON result for the specified Job", tags = "Job")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "GeoJSON Bytes", response = byte[].class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 404, message = "Job or job results not found", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public byte[] downloadJobGeoJson(@ApiParam(value = "ID of the Job", required = true) @PathVariable("id") String id)
			throws UserException {
		return jobService.downloadJobData(id, JobService.DownloadDataType.GEOJSON);
	}

	@RequestMapping(path = "/job/{id}.gpkg", method = RequestMethod.GET, produces = { "application/x-sqlite3" })
	@ResponseBody
	@ApiOperation(value = "Download Detection GeoPackage", notes = "Downloads GeoPackage result for the specified Job", tags = "Job")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "GeoPackage Bytes", response = byte[].class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 404, message = "Job or job results not found", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public byte[] downloadJobGeoPackage(@ApiParam(value = "ID of the Job", required = true) @PathVariable("id") String id)
			throws UserException {
		return jobService.downloadJobData(id, JobService.DownloadDataType.GEOPACKAGE);
	}

	@RequestMapping(path = "/job/{id}.shp.zip", method = RequestMethod.GET, produces = { "application/zip" })
	@ResponseBody
	@ApiOperation(value = "Download Zipped Detection Shapefile", notes = "Downloads Shapefile result for the specified Job", tags = "Job")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "GeoPackage Bytes", response = byte[].class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 404, message = "Job or job results not found", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public byte[] downloadJobShapefile(@ApiParam(value = "ID of the Job", required = true) @PathVariable("id") String id)
			throws UserException {
		return jobService.downloadJobData(id, JobService.DownloadDataType.SHAPEFILE);
	}

	@RequestMapping(path = "/job/searchByInputs", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public List<JobStatus> searchJobsByInputs(@RequestParam(value = "algorithm_id", required = true) String algorithmId,
			@RequestParam(value = "scene_id", required = true) String sceneId) {
		return jobService.searchJobsByInputs(algorithmId, sceneId);
	}
}
