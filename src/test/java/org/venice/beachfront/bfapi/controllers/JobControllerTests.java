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

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

import org.joda.time.DateTime;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.venice.beachfront.bfapi.controllers.JobController.CreateJobBody;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.JobService;
import org.venice.beachfront.bfapi.services.UserProfileService;

public class JobControllerTests {
	@Mock
	private JobService jobService;
	@Mock
	private UserProfileService userProfileService;
	@InjectMocks
	private JobController jobController;

	@Before
	public void setup() throws UserException {
		MockitoAnnotations.initMocks(this);

		UserProfile mockProfile = new UserProfile("Tester", "Tester", "Key", new DateTime());
		Mockito.doReturn(mockProfile).when(userProfileService).getProfileFromAuthentication(Mockito.any());
	}

	@Test
	public void testCreateJob() throws UserException {
		CreateJobBody mockRequest = new CreateJobBody("Job", "Algorithm", "Scene", "Key", true, null);
		jobController.createJob(mockRequest, null);
	}

	@Test
	public void testGetJobs() throws UserException {
		jobController.listJobs(null);
	}

	@Test
	public void testGetJob() throws UserException {
		// Mock
		Job mockJob = new Job("job123", "Test Job", Job.STATUS_SUCCESS, null, new DateTime().minusDays(7), "algId", "algName", "algVersion",
				"scene1", 0.0, 0.0, 0.0, null, true);
		mockJob.setJobId("JobId");
		Mockito.doReturn(mockJob).when(jobService).getJob(Mockito.eq(mockJob.getJobId()));
		// Test
		jobController.getJobById(mockJob.getJobId());
	}

	@Test
	public void testForgetJob() throws UserException {
		// Mock
		Job mockJob = new Job();
		mockJob.setJobId("JobId");
		Mockito.doReturn(mockJob).when(jobService).getJob(Mockito.eq(mockJob.getJobId()));
		Mockito.doReturn(new Confirmation(mockJob.getJobId(), true)).when(jobService).forgetJob(Mockito.eq(mockJob.getJobId()),
				Mockito.eq("Tester"));
		// Test
		Confirmation confirmation = jobController.deleteJob(mockJob.getJobId(), null);
		assertNotNull(confirmation);
		assertEquals(confirmation.getId(), mockJob.getJobId());
		assertEquals(confirmation.getSuccess(), true);
	}

}
