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
package org.venice.beachfront.bfapi.services;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;

import org.apache.commons.io.IOUtils;
import org.joda.time.DateTime;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Matchers;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.test.util.ReflectionTestUtils;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.piazza.StatusMetadata;

import util.PiazzaLogger;

public class JobPollerTests {
	@Mock
	private JobService jobService;
	@Mock
	private PiazzaService piazzaService;
	@Mock
	private PiazzaLogger piazzaLogger;
	@InjectMocks
	private JobPoller jobPoller;

	@Before
	public void setup() {
		MockitoAnnotations.initMocks(this);

		ReflectionTestUtils.setField(this.jobPoller, "POLL_FREQUENCY_SECONDS", 30000);
		ReflectionTestUtils.setField(this.jobPoller, "JOB_TIMEOUT_HOURS", 5);
		ReflectionTestUtils.setField(this.jobPoller, "JOB_ACTIVATION_TIMEOUT_MINUTES", 30);

		// Stop automated polling. Unit tests will call polling explicitly.
		jobPoller.stopPolling();
	}

	@Test
	public void testSuccessfulDetection() throws IOException, UserException {
		// Mock
		Job mockJob = new Job("job123", "Test Job", Job.STATUS_SUCCESS, null, new DateTime().minusDays(7), "algId", "algName", "algVersion",
				"scene1", 0.0, 0.0, 0.0, null, true);
		StatusMetadata mockStatus = new StatusMetadata(Job.STATUS_SUCCESS);
		// Return test GeoJSON for actual data
		InputStream geoJsonData = getClass().getClassLoader()
				.getResourceAsStream(String.format("%s%s%s", "detection", File.separator, "detection.geojson"));
		String mockGeoJson = IOUtils.toString(geoJsonData, "UTF-8");
		Mockito.doReturn(mockGeoJson.getBytes()).when(piazzaService).getJobResultBytesAsGeoJson(Mockito.anyString(),
				Mockito.any());

		// Test
		jobPoller.getTask().processJobStatus(mockJob, mockStatus);

		// Verify no Errors
		Mockito.verify(jobService, Mockito.times(0)).createJobError(Mockito.any(), Mockito.any());
		Mockito.verify(jobService, Mockito.times(1)).updateJob(Mockito.any());
	}

	@Test
	public void testStatus_exceptions() throws IOException, UserException {
		// Mock
		Job mockJob = new Job("job123", "Test Job", Job.STATUS_SUCCESS, null, new DateTime().minusDays(7), "algId", "algName", "algVersion",
				"scene1", 0.0, 0.0, 0.0, null, true);
		StatusMetadata mockStatus = new StatusMetadata(Job.STATUS_SUCCESS);
		// Return test GeoJSON for actual data
//		InputStream geoJsonData = getClass().getClassLoader()
//				.getResourceAsStream(String.format("%s%s%s", "detection", File.separator, "detection.geojson"));
		//String mockGeoJson = IOUtils.toString(geoJsonData, "UTF-8");

		Mockito.when(piazzaService.getJobResultBytesAsGeoJson(Matchers.anyString(), Matchers.anyString()))
				.thenThrow(IOException.class)
				.thenThrow(UserException.class)
				.thenThrow(Exception.class);

		// Test
		mockJob.setStatus(Job.STATUS_PENDING);
		jobPoller.getTask().processJobStatus(mockJob, mockStatus); //IOException
		Assert.assertEquals(Job.STATUS_ERROR, mockJob.getStatus());

		mockJob.setStatus(Job.STATUS_PENDING);
		jobPoller.getTask().processJobStatus(mockJob, mockStatus); //UserException
		Assert.assertEquals(Job.STATUS_ERROR, mockJob.getStatus());

		mockJob.setStatus(Job.STATUS_PENDING);
		jobPoller.getTask().processJobStatus(mockJob, mockStatus); //Exception
		Assert.assertEquals(Job.STATUS_ERROR, mockJob.getStatus());

		mockStatus.setStatus(Job.STATUS_ERROR);
		jobPoller.getTask().processJobStatus(mockJob, mockStatus);
		Assert.assertEquals(Job.STATUS_ERROR, mockJob.getStatus());

	}

	@Test
	public void testPollStatusTask() throws Exception {
		Mockito.when(this.jobPoller.getTask()).thenCallRealMethod();
		JobPoller.PollStatusTask task = this.jobPoller.getTask();

		ArrayList<Job> outstandingJobs = new ArrayList<>();
		outstandingJobs.add(new Job());
		outstandingJobs.get(0).setJobId("job_1");
		outstandingJobs.add(new Job());
		outstandingJobs.get(1).setJobId("job_2");
		outstandingJobs.get(1).setCreatedOn(DateTime.now().minusDays(1));
		outstandingJobs.add(new Job());
		outstandingJobs.get(2).setJobId("job_3");
		outstandingJobs.get(2).setCreatedOn(DateTime.now().minusDays(1));
		Mockito.when(this.jobService.getOutstandingJobs()).thenReturn(outstandingJobs);

		StatusMetadata status_success = new StatusMetadata();
		status_success.setStatus(Job.STATUS_PENDING);

		Mockito.when(this.piazzaService.getJobStatus(Matchers.anyString()))
				.thenReturn(status_success)
				.thenThrow(UserException.class)
				.thenThrow(Exception.class);

		task.run();
	}
}
