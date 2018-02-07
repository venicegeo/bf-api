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

import java.util.Arrays;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.Polygon;
import org.joda.time.DateTime;
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
import org.venice.beachfront.bfapi.database.dao.SceneDao;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobStatus;
import org.venice.beachfront.bfapi.model.JobUser;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.JobService;
import org.venice.beachfront.bfapi.services.JobUserService;
import org.venice.beachfront.bfapi.services.UserProfileService;

/**
 * Main controller class for the JobUser CRUD endpoints.
 * 
 * @version 1.0
 */
@Controller
public class JobUserController {
	@Autowired
	private JobUserService jobUserService;
	@Autowired
	private JobService jobService;
	@Autowired
	private UserProfileService userProfileService;
	@Autowired
	private SceneDao sceneDao;

	@Autowired
	public JobUserController(JobService jobService, UserProfileService userProfileService) {
		this.jobService = jobService;
		this.userProfileService = userProfileService;
	}

	@RequestMapping(path = "/jobuser", method = RequestMethod.POST, consumes = { "application/json" }, produces = { "application/json" })
	@ResponseBody
	public JobUser createJobUser(@RequestBody CreateJobUserBody body) {
		GeometryFactory geometryFactory = new GeometryFactory();

		Coordinate[] coordinates = new Coordinate[5];
		coordinates[0] = new Coordinate(0, 0);
		coordinates[1] = new Coordinate(0, 1);
		coordinates[2] = new Coordinate(1, 1);
		coordinates[3] = new Coordinate(1, 0);
		coordinates[4] = new Coordinate(0, 0);
		Polygon polygonFromCoordinates = geometryFactory.createPolygon(coordinates);
		UserProfile user = userProfileService.getCurrentUserProfile();
		Scene scene = sceneDao.save(new Scene(
				"sceneId",
				DateTime.now(),
				0.0,
				polygonFromCoordinates,
				100,
				"sensorName",
				"uri"
		));
		Job job = jobService.createJob(
				"jobName",
				"XXX",
				"sceneId",
				"algId",
				"planetKey",
				true,
				null
		);
		System.out.println("creating job user");
		return jobUserService.createJobUser(job.getJobId(), user.getUserId());
	}

	@RequestMapping(path = "/jobuser", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public List<JobUser> listJobs() {
		return jobUserService.getJobUsers();
	}

	@RequestMapping(path = "/jobuser/{id}", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public JobUser getJobUserByJobId(@PathVariable("jobId") String jobId) {
		JobUser jobUser = jobUserService.getJobUser(jobId);
		if (jobUser == null) {
			throw new JobUserNotFoundException();
		}
		return jobUser;
	}

	@RequestMapping(path = "/jobuser/{jobId}", method = RequestMethod.DELETE, produces = { "application/json" })
	@ResponseBody
	public Confirmation deleteJob(@PathVariable("jobId") String jobId) {
		JobUser jobUser = jobUserService.getJobUser(jobId);
		return jobUserService.deleteJobUser(jobUser);
	}

	private static class CreateJobUserBody {
		public final String jobId;
		public final String userId;

		@JsonCreator
		public CreateJobUserBody(@JsonProperty(value = "job_id", required = true) String jobId,
				@JsonProperty(value = "user_id", required = true) String userId) {
			this.jobId = jobId;
			this.userId = userId;
		}
	}

	@ResponseStatus(value = HttpStatus.NOT_FOUND)
	private static class JobUserNotFoundException extends RuntimeException {
		private static final long serialVersionUID = 1L;
	}

	@RequestMapping(path = "/jobuser/searchByInputs", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public List<JobUser> searchJobUsersByInputs(@RequestParam(value = "user_id", required = true) String userId) {
		return jobUserService.searchByUser(userId);
	}
}
