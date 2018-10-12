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

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;

import org.apache.commons.io.IOUtils;
import org.geotools.geojson.geom.GeometryJSON;
import org.joda.time.DateTime;
import org.joda.time.Seconds;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Matchers;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.mockito.Spy;
import org.springframework.http.HttpStatus;
import org.springframework.test.util.ReflectionTestUtils;
import org.venice.beachfront.bfapi.database.dao.DetectionDao;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.database.dao.JobErrorDao;
import org.venice.beachfront.bfapi.database.dao.JobUserDao;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.JobError;
import org.venice.beachfront.bfapi.model.JobUser;
import org.venice.beachfront.bfapi.model.JobUserPK;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.piazza.StatusMetadata;
import org.venice.beachfront.bfapi.services.converter.GeoPackageConverter;
import org.venice.beachfront.bfapi.services.converter.ShapefileConverter;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vividsolutions.jts.geom.Geometry;

import util.PiazzaLogger;

public class JobServiceTests {
	@Mock
	private JobDao jobDao;
	@Mock
	private AlgorithmService algorithmService;
	@Mock
	private SceneService sceneService;
	@Mock
	private JobErrorDao jobErrorDao;
	@Mock
	private PiazzaService piazzaService;
	@Mock
	private JobUserDao jobUserDao;
	@Mock
	private DetectionDao detectionDao;
	@Mock
	private UserProfileService userProfileService;
	@Mock
	private PiazzaLogger piazzaLogger;
	@Mock
	private GeoPackageConverter geoPackageConverter;
	@Mock
	private ShapefileConverter shpConverter;
	@Spy
	private ObjectMapper objectMapper;
	@InjectMocks
	private JobService jobService;

	@Before
	public void setup() {
		MockitoAnnotations.initMocks(this);

		ReflectionTestUtils.setField(jobService, "blockRedundantJobCheck", false);
	}

	@Test
	public void testCreateJob() throws UserException {
		// Mock Scene and Algorithm
		String serviceId = "service123";
		String creatorId = "tester123";
		Algorithm mockAlgorithm = new Algorithm("Description", "Interface", 10, "Name", serviceId, "1.0.0");
		Mockito.doReturn(mockAlgorithm).when(algorithmService).getAlgorithm(Mockito.eq(serviceId));
		Scene mockScene = new Scene("scene123", new DateTime(), 10, null, 10, "Sensor", "URI");
		Mockito.doReturn(mockScene).when(sceneService).getScene(Mockito.eq("scene123"), Mockito.anyString(), Mockito.anyBoolean());
		Mockito.doReturn(CompletableFuture.completedFuture(mockScene)).when(sceneService).asyncGetActiveScene(Mockito.eq("scene123"),
				Mockito.anyString(), Mockito.anyBoolean());
		Mockito.doReturn(mockScene).when(sceneService).getSceneFromLocalDatabase(Mockito.eq("scene123"));
		// No redundant jobs
		Mockito.doReturn(new ArrayList<Job>()).when(jobDao)
				.findBySceneIdAndAlgorithmIdAndAlgorithmVersionAndComputeMaskAndStatusAndSeedJobIdIsNull(Mockito.eq(mockScene.getSceneId()),
						Mockito.eq(serviceId), Mockito.eq(mockAlgorithm.getVersion()), Mockito.any(), Mockito.any());

		// Test
		String jobName = "Test Job";
		Job job = jobService.createJob(jobName, creatorId, mockScene.getSceneId(), serviceId, null, true, null);

		// Verify
		assertNotNull(job);
		assertEquals(job.getAlgorithmId(), serviceId);
		assertEquals(job.getAlgorithmName(), mockAlgorithm.getName());
		assertEquals(job.getAlgorithmVersion(), mockAlgorithm.getVersion());
		assertEquals(job.getCreatedByUserId(), creatorId);
		assertTrue(Seconds.secondsBetween(new DateTime(), job.getCreatedOn()).getSeconds() <= 5);
		assertEquals(job.getJobName(), jobName);
		assertEquals(job.getSceneId(), mockScene.getSceneId());
		assertEquals(job.getStatus(), Job.STATUS_ACTIVATING);
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
		Mockito.doReturn(mockJobs).when(jobDao).findBySceneIdAndAlgorithmIdAndAlgorithmVersionAndComputeMaskAndStatusAndSeedJobIdIsNull(
				Mockito.eq(sceneId), Mockito.eq(serviceId), Mockito.eq(mockAlgorithm.getVersion()), Mockito.eq(true),
				Mockito.eq(Job.STATUS_SUCCESS));
		Scene mockScene = new Scene(sceneId, new DateTime(), 10, null, 10, "Sensor", "URI");
		Mockito.doReturn(mockScene).when(sceneService).getSceneFromLocalDatabase(Mockito.eq("scene123"));

		// Test
		String creatorId = "New Creator";
		Job job = jobService.createJob("Test Job", creatorId, sceneId, serviceId, null, true, null);

		// Verify
		assertNotNull(job);
		assertEquals(job.getSeedJobId(), mockJob.getJobId());
		assertEquals(job.getAlgorithmId(), serviceId);
		assertEquals(job.getAlgorithmName(), mockAlgorithm.getName());
		assertEquals(job.getAlgorithmVersion(), mockAlgorithm.getVersion());
		assertEquals(job.getSceneId(), mockScene.getSceneId());
		assertEquals(job.getStatus(), Job.STATUS_SUCCESS);
	}

	@Test
	public void testJobGeoJson() throws UserException, IOException {
		// Mock two Jobs with 2 corresponding scenes
		List<Job> mockJobs = new ArrayList<Job>();
		Job mockJob = new Job("job123", "Test Job", Job.STATUS_SUCCESS, null, new DateTime().minusDays(7), "algId", "algName", "algVersion",
				"scene1", 0.0, 0.0, 0.0, null, true);
		mockJobs.add(mockJob);
		mockJob = new Job("job321", "Test Job", Job.STATUS_SUCCESS, null, new DateTime().minusDays(7), "algId", "algName", "algVersion",
				"scene1", 0.0, 0.0, 0.0, null, true);
		mockJobs.add(mockJob);
		// Mock a scene with some GeoJSON Geometry
		String geometryString = IOUtils.toString(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "scene", File.separator, "geometry.json")),
				"UTF-8");
		GeometryJSON geometryJson = new GeometryJSON();
		Geometry geometry = geometryJson.read(geometryString);
		Scene mockScene = new Scene("scene123", new DateTime(), 10, geometry, 10, "Sensor", "URI");
		Mockito.doReturn(mockScene).when(sceneService).getSceneFromLocalDatabase(Mockito.eq("scene1"));
		// Test
		JsonNode geoJson = jobService.getJobsGeoJson(mockJobs);
		// Verify
		assertNotNull(geoJson);
		JsonNode featureCollection = geoJson.get("jobs");
		JsonNode features = featureCollection.get("features");
		assertEquals(featureCollection.get("type").textValue(), "FeatureCollection");
		assertEquals(features.size(), 2);
		assertEquals(features.get(0).get("id").textValue(), "job123");
		assertEquals(features.get(0).get("type").textValue(), "Feature");
		assertEquals(features.get(0).get("geometry").get("type").textValue(), "Polygon");
		assertEquals(features.get(0).get("geometry").get("coordinates").get(0).size(), geometry.getNumPoints());
		assertEquals(features.get(0).get("properties").get("job_id").textValue(), "job123");
		assertEquals(features.get(0).get("properties").get("status").textValue(), "Success");
		assertEquals(features.get(0).get("properties").get("compute_mask").booleanValue(), true);
		assertEquals(features.get(1).get("id").textValue(), "job321");
		assertEquals(features.get(1).get("type").textValue(), "Feature");
		assertEquals(features.get(1).get("geometry").get("type").textValue(), "Polygon");
		assertEquals(features.get(1).get("geometry").get("coordinates").get(0).size(), geometry.getNumPoints());
		assertEquals(features.get(1).get("properties").get("job_id").textValue(), "job321");
		assertEquals(features.get(1).get("properties").get("status").textValue(), "Success");
		assertEquals(features.get(1).get("properties").get("compute_mask").booleanValue(), true);
	}

	@Test
	public void testDownloadJobData_StatusError() throws UserException {
		// Setup
		StatusMetadata mockStatus = Mockito.mock(StatusMetadata.class);
		Job mockJob = new Job("job123", "Test Job", Job.STATUS_SUCCESS, null, new DateTime().minusDays(7), "alg123", "alg", "1.0",
				"scene123", null, null, null, null, true);
		Mockito.when(this.jobDao.findByJobId(Mockito.anyString())).thenReturn(mockJob);
		Mockito.when(mockStatus.isStatusError()).thenReturn(true);
		Mockito.when(mockStatus.isStatusIncomplete()).thenReturn(false);
		Mockito.when(mockStatus.isStatusSuccess()).thenReturn(false);
		Mockito.when(this.piazzaService.getJobStatus("test-job-id-123")).thenReturn(mockStatus);

		// Test
		try {
			this.jobService.downloadJobData("test-job-id-123", null);
			Assert.fail("Expected job result download to fail, but it did not");
		} catch (UserException ex) {
			Assert.assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, ex.getRecommendedStatusCode());
		}
	}

	@Test
	public void testDownloadJobData_StatusIncomplete() throws UserException {
		// Setup
		Job mockJob = new Job("job123", "Test Job", Job.STATUS_ACTIVATING, null, new DateTime().minusDays(7), "alg123", "alg", "1.0",
				"scene123", null, null, null, null, true);
		Mockito.when(this.jobDao.findByJobId(Mockito.anyString())).thenReturn(mockJob);
		StatusMetadata mockStatus = Mockito.mock(StatusMetadata.class);
		Mockito.when(mockStatus.isStatusError()).thenReturn(false);
		Mockito.when(mockStatus.isStatusIncomplete()).thenReturn(true);
		Mockito.when(mockStatus.isStatusSuccess()).thenReturn(false);
		Mockito.when(this.piazzaService.getJobStatus("test-job-id-123")).thenReturn(mockStatus);

		// Test and asserts
		try {
			this.jobService.downloadJobData("test-job-id-123", null);
			Assert.fail("Expected job result download to fail, but it did not");
		} catch (UserException ex) {
			Assert.assertEquals(HttpStatus.NOT_FOUND, ex.getRecommendedStatusCode());
		}
	}

	@Test
	public void testDownloadJobData_StatusSuccess() throws UserException {
		// Setup
		StatusMetadata mockStatus = Mockito.mock(StatusMetadata.class);
		Mockito.when(mockStatus.isStatusError()).thenReturn(false);
		Mockito.when(mockStatus.isStatusIncomplete()).thenReturn(false);
		Mockito.when(mockStatus.isStatusSuccess()).thenReturn(true);
		Mockito.when(mockStatus.getDataId()).thenReturn("data-id-321");
		Mockito.when(this.piazzaService.getJobStatus("test-job-id-123")).thenReturn(mockStatus);
		Job mockJob = new Job("job123", "Test Job", Job.STATUS_SUCCESS, null, new DateTime().minusDays(7), "alg123", "alg", "1.0",
				"scene123", null, null, null, null, true);
		Mockito.when(jobDao.findByJobId(Mockito.anyString())).thenReturn(mockJob);

		String mockJSON = "{\"foo\": 123}";
		byte[] mockJSONResult = mockJSON.getBytes();
		Mockito.when(this.piazzaService.getJobResultBytesAsGeoJson("data-id-321", "test-job-id-123")).thenReturn(mockJSONResult);
		Mockito.when(this.detectionDao.findFullDetectionGeoJson("test-job-id-123")).thenReturn(mockJSON);
		byte[] mockGeoPackageResult = "mock-geopackage-result".getBytes();
		Mockito.when(this.geoPackageConverter.apply(Mockito.any())).thenReturn(mockGeoPackageResult);
		byte[] mockShapefileResult = "mock-shapefile-result".getBytes();
		Mockito.when(this.shpConverter.apply(Mockito.any())).thenReturn(mockShapefileResult);

		// Test
		byte[] actualJSONResult = this.jobService.downloadJobData("test-job-id-123", JobService.DownloadDataType.GEOJSON);
		byte[] actualGeoPackageResult = this.jobService.downloadJobData("test-job-id-123", JobService.DownloadDataType.GEOPACKAGE);
		byte[] actualShapefileResult = this.jobService.downloadJobData("test-job-id-123", JobService.DownloadDataType.SHAPEFILE);

		// Asserts
		Assert.assertArrayEquals(mockJSONResult, actualJSONResult);
		Assert.assertArrayEquals(mockGeoPackageResult, actualGeoPackageResult);
		Assert.assertArrayEquals(mockShapefileResult, actualShapefileResult);
	}

	@Test
	public void testCreateJobError() {

		this.jobService.createJobError(new Job(), "the_job_error");
		Mockito.verify(this.jobErrorDao, Mockito.times(1)).save(Matchers.any(JobError.class));
	}

	@Test
	public void testSearchJobsByInputs() {
		ArrayList<Job> jobs = new ArrayList<>();
		jobs.add(new Job());
		jobs.add(new Job());
		Mockito.when(this.jobDao.findByAlgorithmIdAndSceneId("my_algorithm_id", "my_scene_id")).thenReturn(jobs);
		Assert.assertEquals(jobs.size(), this.jobService.searchJobsByInputs("my_algorithm_id", "my_scene_id").size());
	}

	@Test
	public void testGetJobsForUser() {

		ArrayList<JobUser> jobUsers = new ArrayList<>();
		jobUsers.add(new JobUser());
		jobUsers.get(0).setjobUserPK(new JobUserPK());
		jobUsers.add(new JobUser());
		jobUsers.get(1).setjobUserPK(new JobUserPK());

		Mockito.when(this.jobUserDao.findByJobUserPK_User_UserId("user_1")).thenReturn(jobUsers);

		List<Job> result = this.jobService.getJobsForUser("user_1");
		Assert.assertEquals(jobUsers.size(), result.size());
	}

	@Test
	public void testGetOutstandingJobs() {
		ArrayList<Job> jobList = new ArrayList<>();

		jobList.add(new Job());
		jobList.add(new Job());
		jobList.add(new Job());

		Mockito.when(this.jobDao.findByStatusIn(Matchers.anyList())).thenReturn(jobList);

		List<Job> result = this.jobService.getOutstandingJobs();

		Assert.assertEquals(jobList.size(), result.size());
	}

	@Test
	public void testForgetJob() {
		Mockito.when(this.jobUserDao.findByJobUserPK_Job_JobIdAndJobUserPK_User_UserId("job_1", "user_1")).thenReturn(new JobUser());

		Assert.assertTrue(this.jobService.forgetJob("job_1", "user_1").getSuccess());
		Assert.assertFalse(this.jobService.forgetJob("job_1", "user_2").getSuccess());
		Assert.assertFalse(this.jobService.forgetJob("job_2", "user_1").getSuccess());

		Mockito.verify(this.jobUserDao, Mockito.times(1)).delete(Matchers.any(JobUser.class));
	}

	@Test
	public void testForgetAllJobs() throws Exception {
		JobUser jobUser = new JobUser();
		jobUser.setjobUserPK(new JobUserPK());
		jobUser.getJobUserPK().setJob(new Job());

		ArrayList<JobUser> jList = new ArrayList<>();
		jList.add(jobUser);

		Mockito.when(this.jobUserDao.findByJobUserPK_User_UserId(Matchers.anyString())).thenReturn(jList);

		Mockito.when(this.jobUserDao.findByJobUserPK_Job_JobIdAndJobUserPK_User_UserId(Matchers.anyString(), Matchers.anyString()))
				.thenReturn(jobUser).thenReturn(null);

		Assert.assertTrue(this.jobService.forgetAllJobs("user_1").getSuccess());

		try {
			this.jobService.forgetAllJobs("user_2");
			Assert.fail("Expected an exception.");
		} catch (UserException ex) {
			// Good
		}
	}

}
