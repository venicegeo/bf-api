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
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.io.IOUtils;
import org.geotools.geojson.geom.GeometryJSON;
import org.joda.time.DateTime;
import org.joda.time.Days;
import org.joda.time.Seconds;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.mockito.Spy;
import org.springframework.test.util.ReflectionTestUtils;
import org.venice.beachfront.bfapi.database.dao.DetectionDao;
import org.venice.beachfront.bfapi.database.dao.JobDao;
import org.venice.beachfront.bfapi.database.dao.JobErrorDao;
import org.venice.beachfront.bfapi.database.dao.JobUserDao;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;

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
		JsonNode jobParent = jobService.createJob(jobName, creatorId, mockScene.getSceneId(), serviceId, null, true, null);
		JsonNode job = jobParent.get("job");

		// Verify
		assertNotNull(job);
		assertEquals(job.get("job_id").textValue(), jobId);
		assertEquals(job.get("algorithm_id").textValue(), serviceId);
		assertEquals(job.get("algorithm_name").textValue(), mockAlgorithm.getName());
		assertEquals(job.get("algorithm_version").textValue(), mockAlgorithm.getVersion());
		assertEquals(job.get("created_by").textValue(), creatorId);
		assertTrue(Seconds.secondsBetween(new DateTime(), new DateTime(job.get("created_on").textValue())).getSeconds() <= 5);
		assertEquals(job.get("job_name").textValue(), jobName);
		assertEquals(job.get("scene_id").textValue(), mockScene.getSceneId());
		assertEquals(job.get("status").textValue(), Job.STATUS_SUBMITTED);
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
		JsonNode jobParent = jobService.createJob("Test Job", creatorId, sceneId, serviceId, null, true, null);
		JsonNode job = jobParent.get("job");

		// Verify
		assertNotNull(job);
		assertEquals(job.get("job_id").textValue(), mockJob.getJobId());
		assertEquals(job.get("algorithm_id").textValue(), serviceId);
		assertEquals(job.get("algorithm_name").textValue(), mockAlgorithm.getName());
		assertEquals(job.get("algorithm_version").textValue(), mockAlgorithm.getVersion());
		assertNotEquals(job.get("created_by").textValue(), creatorId);
		assertTrue(Days.daysBetween(new DateTime(), new DateTime(job.get("created_on"))).getDays() <= 7);
		assertEquals(job.get("scene_id").textValue(), sceneId);
		assertEquals(job.get("status").textValue(), Job.STATUS_SUCCESS);
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
}
