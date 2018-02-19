package org.venice.beachfront.bfapi.services;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.util.ArrayList;

import org.joda.time.DateTime;
import org.joda.time.Days;
import org.joda.time.Seconds;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.venice.beachfront.bfapi.database.dao.DetectionDao;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.database.dao.JobUserDao;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;

public class JobServiceTests {
	@Mock
	private JobDao jobDao;
	@Mock
	private AlgorithmService algorithmService;
	@Mock
	private SceneService sceneService;
	@Mock
	private PiazzaService piazzaService;
	@Mock
	private JobUserDao jobUserDao;
	@Mock
	private DetectionDao detectionDao;
	@Mock
	private UserProfileService userProfileService;
	@InjectMocks
	private JobService jobService;

	@Before
	public void setup() {
		MockitoAnnotations.initMocks(this);
	}

	@Test
	public void testCreateJob() throws UserException {
		// Mock Scene and Algorithm
		String serviceId = "service123";
		String creatorId = "tester123";
		Algorithm mockAlgorithm = new Algorithm("Description", "Interface", 10, "Name", serviceId, "1.0.0");
		Mockito.doReturn(mockAlgorithm).when(algorithmService).getAlgorithm(Mockito.eq(serviceId));
		Scene mockScene = new Scene("scene123", new DateTime(), 10, null, 10, "Sensor", "URI");
		Mockito.doReturn(mockScene).when(sceneService).getScene(Mockito.eq("scene123"), Mockito.any(), Mockito.anyBoolean());
		// No redundant jobs
		Mockito.doReturn(new ArrayList<Job>()).when(jobDao).findBySceneIdAndAlgorithmIdAndAlgorithmVersionAndComputeMaskAndStatus(
				Mockito.eq(mockScene.getSceneId()), Mockito.eq(serviceId), Mockito.eq(mockAlgorithm.getVersion()), Mockito.any(),
				Mockito.any());
		// Mock Piazza Response
		String jobId = "job123";
		Mockito.doReturn(jobId).when(piazzaService).execute(Mockito.eq(serviceId), Mockito.any(), Mockito.any(), Mockito.any(),
				Mockito.eq(creatorId));

		// Test
		String jobName = "Test Job";
		Job job = jobService.createJob(jobName, creatorId, mockScene.getSceneId(), serviceId, null, true, null);

		// Verify
		assertNotNull(job);
		assertEquals(job.getJobId(), jobId);
		assertEquals(job.getAlgorithmId(), serviceId);
		assertEquals(job.getAlgorithmName(), mockAlgorithm.getName());
		assertEquals(job.getAlgorithmVersion(), mockAlgorithm.getVersion());
		assertEquals(job.getCreatedByUserId(), creatorId);
		assertTrue(Seconds.secondsBetween(new DateTime(), job.getCreatedOn()).getSeconds() <= 5);
		assertEquals(job.getJobName(), jobName);
		assertEquals(job.getSceneId(), mockScene.getSceneId());
		assertEquals(job.getStatus(), Job.STATUS_SUBMITTED);
	}

	@Test
	public void testCreateRedundantJob() throws UserException {
		// Mock
		String serviceId = "service123";
		String sceneId = "scene123";
		Algorithm mockAlgorithm = new Algorithm("Description", "Interface", 10, "Name", serviceId, "1.0.0");
		Mockito.doReturn(mockAlgorithm).when(algorithmService).getAlgorithm(Mockito.eq(serviceId));
		Job mockJob = new Job("job123", "Test Job", Job.STATUS_SUCCESS, null, new DateTime().minusDays(7), mockAlgorithm.getServiceId(),
				mockAlgorithm.getName(), mockAlgorithm.getVersion(), sceneId, null, null, null, null, true);
		// Return Job on redundant check
		ArrayList<Job> mockJobs = new ArrayList<Job>();
		mockJobs.add(mockJob);
		Mockito.doReturn(mockJobs).when(jobDao).findBySceneIdAndAlgorithmIdAndAlgorithmVersionAndComputeMaskAndStatus(Mockito.eq(sceneId),
				Mockito.eq(serviceId), Mockito.eq(mockAlgorithm.getVersion()), Mockito.eq(true), Mockito.eq(Job.STATUS_SUCCESS));

		// Test
		String creatorId = "New Creator";
		Job job = jobService.createJob("Test Job", creatorId, sceneId, serviceId, null, true, null);

		// Verify
		assertNotNull(job);
		assertEquals(job.getJobId(), mockJob.getJobId());
		assertEquals(job.getAlgorithmId(), serviceId);
		assertEquals(job.getAlgorithmName(), mockAlgorithm.getName());
		assertEquals(job.getAlgorithmVersion(), mockAlgorithm.getVersion());
		assertNotEquals(job.getCreatedByUserId(), creatorId);
		assertTrue(Days.daysBetween(new DateTime(), job.getCreatedOn()).getDays() <= 7);
		assertEquals(job.getSceneId(), sceneId);
		assertEquals(job.getStatus(), Job.STATUS_SUCCESS);
	}
}
