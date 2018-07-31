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
import static org.junit.Assert.assertNull;
import static org.junit.Assert.fail;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;

import org.joda.time.DateTime;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.mockito.invocation.InvocationOnMock;
import org.mockito.stubbing.Answer;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import org.venice.beachfront.bfapi.database.dao.SceneDao;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;

import util.PiazzaLogger;

public class SceneServiceTests {
	@Mock
	private RestTemplate restTemplate;
	@Mock
	private PiazzaLogger piazzaLogger;
	@Mock
	private ExecutorService executor;
	@Mock
	private SceneDao sceneDao;

	@InjectMocks
	private SceneService sceneService;

	@Before
	public void setup() {
		MockitoAnnotations.initMocks(this);
		ReflectionTestUtils.setField(this.sceneService, "bfDomain", "bf-test.localdomain");
		ReflectionTestUtils.setField(this.sceneService, "iaBrokerProtocol", "https");
		ReflectionTestUtils.setField(this.sceneService, "iaBrokerServer", "bf-ia-broker-test.localdomain");
		ReflectionTestUtils.setField(this.sceneService, "iaBrokerPort", 443);
	}

	@Test
	public void testGetSceneInputFileNames() {
		Scene scene = new Scene();
		List<String> inputFileNames;

		scene.setSceneId("rapideye:abcd");
		inputFileNames = this.sceneService.getSceneInputFileNames(scene);
		assertEquals(Arrays.asList("multispectral.TIF"), inputFileNames);

		scene.setSceneId("planetscope:abcd");
		inputFileNames = this.sceneService.getSceneInputFileNames(scene);
		assertEquals(Arrays.asList("multispectral.TIF"), inputFileNames);

		scene.setSceneId("landsat:abcd");
		inputFileNames = this.sceneService.getSceneInputFileNames(scene);
		assertEquals(Arrays.asList("coastal.TIF", "swir1.TIF"), inputFileNames);

		scene.setSceneId("sentinel:abcd");
		inputFileNames = this.sceneService.getSceneInputFileNames(scene);
		assertEquals(Arrays.asList("coastal.JP2", "swir1.JP2"), inputFileNames);

		scene.setSceneId("bogus:abcd");
		inputFileNames = this.sceneService.getSceneInputFileNames(scene);
		assertEquals(0, inputFileNames.size());

		scene.setSceneId("");
		inputFileNames = this.sceneService.getSceneInputFileNames(scene);
		assertEquals(0, inputFileNames.size());
	}

	@Test
	public void testGetSceneInputURLs() {
		ObjectNode bands = JsonNodeFactory.instance.objectNode();
		bands.set("coastal", JsonNodeFactory.instance.textNode("COASTAL_URL"));
		bands.set("blue", JsonNodeFactory.instance.textNode("BLUE_URL"));
		bands.set("nir", JsonNodeFactory.instance.textNode("NIR_URL"));
		bands.set("swir1", JsonNodeFactory.instance.textNode("SWIR1_URL"));
		JsonNode properties = JsonNodeFactory.instance.objectNode().set("bands", bands);
		((ObjectNode) properties).put("location", "LOCATION_URL");
		JsonNode rawJson = JsonNodeFactory.instance.objectNode().set("properties", properties);

		Scene scene = new Scene();
		scene.setUri("SCENE_URL");
		scene.setRawJson(rawJson);
		List<String> inputURLs;

		scene.setSceneId("rapideye:abcd");
		inputURLs = this.sceneService.getSceneInputURLs(scene);
		assertEquals(Arrays.asList("LOCATION_URL"), inputURLs);

		scene.setSceneId("planetscope:abcd");
		inputURLs = this.sceneService.getSceneInputURLs(scene);
		assertEquals(Arrays.asList("LOCATION_URL"), inputURLs);

		scene.setSceneId("landsat:abcd");
		inputURLs = this.sceneService.getSceneInputURLs(scene);
		assertEquals(Arrays.asList("COASTAL_URL", "SWIR1_URL"), inputURLs);

		scene.setSceneId("sentinel:abcd");
		inputURLs = this.sceneService.getSceneInputURLs(scene);
		assertEquals(Arrays.asList("BLUE_URL", "NIR_URL"), inputURLs);

		scene.setSceneId("bogus:abcd");
		inputURLs = this.sceneService.getSceneInputURLs(scene);
		assertEquals(0, inputURLs.size());

		scene.setSceneId("");
		inputURLs = this.sceneService.getSceneInputURLs(scene);
		assertEquals(0, inputURLs.size());
	}

	@Test
	public void testGetDownloadUri() {
		Scene scene = new Scene();
		scene.setSceneId("SCENE_ID");

		URI sceneDownloadUri = this.sceneService.getDownloadUri(scene, "api-abc-123");
		assertEquals("https://bf-api.bf-test.localdomain/scene/SCENE_ID/download?planet_api_key=api-abc-123", sceneDownloadUri.toString());
	}

	@Test
	public void testActivateSceneSuccess() throws UserException {
		Scene scene = new Scene();
		scene.setStatus(Scene.STATUS_INACTIVE);
		scene.setSceneId("rapideye:EXTERNAL_ID");

		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(Object.class))).then(new Answer<ResponseEntity<?>>() {
			public ResponseEntity<?> answer(InvocationOnMock invocation) {
				Object[] args = invocation.getArguments();
				assertEquals(URI.class, args[0].getClass());
				assertEquals("https://bf-ia-broker-test.localdomain:443/planet/activate/rapideye/EXTERNAL_ID?PL_API_KEY=api-abc-123",
						((URI) args[0]).toString());
				return new ResponseEntity<Object>(null, HttpStatus.OK);
			}
		});

		this.sceneService.activateScene(scene, "api-abc-123");
	}

	@Test
	public void testActivateSceneNotInactiveLeadsToNoop() throws UserException {
		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(Object.class))).then(new Answer<ResponseEntity<?>>() {
			public ResponseEntity<?> answer(InvocationOnMock invocation) {
				fail("this should not have been called");
				return null;
			}
		});

		Scene scene = new Scene();
		scene.setStatus(Scene.STATUS_ACTIVE);
		this.sceneService.activateScene(scene, "api-abc-123");

		scene.setStatus(Scene.STATUS_ACTIVATING);
		this.sceneService.activateScene(scene, "api-abc-123");
	}

	@Test
	public void testActivateScene401() {
		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(Object.class))).then(new Answer<ResponseEntity<?>>() {
			public ResponseEntity<?> answer(InvocationOnMock invocation) {
				throw new HttpClientErrorException(HttpStatus.UNAUTHORIZED);
			}
		});

		Scene scene = new Scene();
		scene.setStatus(Scene.STATUS_INACTIVE);
		scene.setSceneId("rapideye:EXTERNAL_ID");
		try {
			this.sceneService.activateScene(scene, "api-abc-123");
			fail("activation should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.BAD_REQUEST, ex.getRecommendedStatusCode());
			return;
		}
	}

	@Test
	public void testActivateScene404() {
		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(Object.class))).then(new Answer<ResponseEntity<?>>() {
			public ResponseEntity<?> answer(InvocationOnMock invocation) {
				throw new HttpClientErrorException(HttpStatus.NOT_FOUND);
			}
		});

		Scene scene = new Scene();
		scene.setStatus(Scene.STATUS_INACTIVE);
		scene.setSceneId("rapideye:EXTERNAL_ID");
		try {
			this.sceneService.activateScene(scene, "api-abc-123");
			fail("activation should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.NOT_FOUND, ex.getRecommendedStatusCode());
			return;
		}
	}

	@Test
	public void testActivateScene502() {
		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(Object.class))).then(new Answer<ResponseEntity<?>>() {
			public ResponseEntity<?> answer(InvocationOnMock invocation) {
				throw new HttpServerErrorException(HttpStatus.BAD_GATEWAY);
			}
		});

		Scene scene = new Scene();
		scene.setStatus(Scene.STATUS_INACTIVE);
		scene.setSceneId("rapideye:EXTERNAL_ID");
		try {
			this.sceneService.activateScene(scene, "api-abc-123");
			fail("activation should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.BAD_GATEWAY, ex.getRecommendedStatusCode());
		}
	}

	@Test
	public void testGetSceneRapideyeWithTidesSuccess() throws UserException, IOException {
		JsonNode responseJson = new ObjectMapper().readTree(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "scene", File.separator, "getScene.json")));

		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(JsonNode.class)))
				.then(new Answer<ResponseEntity<JsonNode>>() {
					public ResponseEntity<JsonNode> answer(InvocationOnMock invocation) {
						Object[] args = invocation.getArguments();
						assertEquals(URI.class, args[0].getClass());
						assertEquals(
								"https://bf-ia-broker-test.localdomain:443/planet/rapideye/EXTERNAL_ID?PL_API_KEY=api-abc-123&tides=true",
								((URI) args[0]).toString());
						return new ResponseEntity<JsonNode>(responseJson, HttpStatus.OK);
					}
				});

		Scene scene = this.sceneService.getScene("rapideye:EXTERNAL_ID", "api-abc-123", true);

		assertEquals("EXTERNAL_ID", scene.getExternalId());
		assertEquals(0.1, scene.getCloudCover(), 0.0001);
		assertEquals(3, scene.getResolution());
		assertEquals(DateTime.parse("2018-02-26T07:28:08Z"), scene.getCaptureTime());
		assertEquals("mockSensorName", scene.getSensorName());
		assertEquals("https://bf-ia-broker-test.localdomain:443/planet/rapideye/EXTERNAL_ID", scene.getUri());
		assertEquals(Scene.STATUS_INACTIVE, scene.getStatus());
		assertEquals(0.5, scene.getTide(), 0.0001);
		assertEquals(0.1, scene.getTideMin24H(), 0.0001);
		assertEquals(0.8, scene.getTideMax24H(), 0.0001);
	}

	@Test
	public void testGetSceneLandsatWithoutTidesSuccess() throws UserException, IOException {
		JsonNode responseJson = new ObjectMapper().readTree(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "scene", File.separator, "getScene.json")));

		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(JsonNode.class)))
				.then(new Answer<ResponseEntity<JsonNode>>() {
					public ResponseEntity<JsonNode> answer(InvocationOnMock invocation) {
						Object[] args = invocation.getArguments();
						assertEquals(URI.class, args[0].getClass());
						assertEquals(
								"https://bf-ia-broker-test.localdomain:443/planet/landsat/EXTERNAL_ID?PL_API_KEY=api-abc-123&tides=false",
								((URI) args[0]).toString());
						return new ResponseEntity<JsonNode>(responseJson, HttpStatus.OK);
					}
				});

		Scene scene = this.sceneService.getScene("landsat:EXTERNAL_ID", "api-abc-123", false);

		assertEquals("EXTERNAL_ID", scene.getExternalId());
		assertEquals(0.1, scene.getCloudCover(), 0.0001);
		assertEquals(3, scene.getResolution());
		assertEquals(DateTime.parse("2018-02-26T07:28:08Z"), scene.getCaptureTime());
		assertEquals("mockSensorName", scene.getSensorName());
		assertEquals("https://bf-ia-broker-test.localdomain:443/planet/landsat/EXTERNAL_ID", scene.getUri());
		assertEquals(Scene.STATUS_ACTIVE, scene.getStatus()); // This is the big difference from rapideye; landsat
																// should always be active
		assertNull(scene.getTide());
		assertNull(scene.getTideMin24H());
		assertNull(scene.getTideMax24H());
	}

	@Test
	public void testGetLandsatScene() throws UserException, IOException {
		// Mock
		JsonNode responseJson = new ObjectMapper().readTree(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "scene", File.separator, "getLandsatScene.json")));
		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(JsonNode.class)))
				.then(new Answer<ResponseEntity<JsonNode>>() {
					public ResponseEntity<JsonNode> answer(InvocationOnMock invocation) {
						Object[] args = invocation.getArguments();
						assertEquals(URI.class, args[0].getClass());
						assertEquals(
								"https://bf-ia-broker-test.localdomain:443/planet/landsat/EXTERNAL_ID?PL_API_KEY=api-abc-123&tides=false",
								((URI) args[0]).toString());
						return new ResponseEntity<JsonNode>(responseJson, HttpStatus.OK);
					}
				});
		// Test
		Scene scene = this.sceneService.getScene("landsat:EXTERNAL_ID", "api-abc-123", false);
		// Verify
		assertEquals("test", scene.getExternalId());
		assertEquals(50, scene.getCloudCover(), 0.0001);
		assertEquals(30, scene.getResolution());
		assertEquals(DateTime.parse("2016-09-30T09:45:02.625661Z"), scene.getCaptureTime());
		assertEquals("Landsat8", scene.getSensorName());
		assertEquals(Scene.STATUS_ACTIVE, scene.getStatus()); // This is the big difference from rapideye; landsat
																// should always be active
	}

	@Test
	public void testGetScene401() {
		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(JsonNode.class))).then(new Answer<ResponseEntity<?>>() {
			public ResponseEntity<?> answer(InvocationOnMock invocation) {
				throw new HttpClientErrorException(HttpStatus.UNAUTHORIZED);
			}
		});

		try {
			this.sceneService.getScene("landsat:EXTERNAL_ID", "api-abc-123", false);
			fail("get scene should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.BAD_REQUEST, ex.getRecommendedStatusCode());
		}
	}

	@Test
	public void testGetScene404() {
		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(JsonNode.class))).then(new Answer<ResponseEntity<?>>() {
			public ResponseEntity<?> answer(InvocationOnMock invocation) {
				throw new HttpClientErrorException(HttpStatus.NOT_FOUND);
			}
		});

		try {
			this.sceneService.getScene("landsat:EXTERNAL_ID", "api-abc-123", false);
			fail("get scene should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.NOT_FOUND, ex.getRecommendedStatusCode());
		}
	}

	@Test
	public void testGetScene502() {
		Mockito.when(this.restTemplate.getForEntity(Mockito.any(), Mockito.eq(JsonNode.class))).then(new Answer<ResponseEntity<?>>() {
			public ResponseEntity<?> answer(InvocationOnMock invocation) {
				throw new HttpServerErrorException(HttpStatus.BAD_GATEWAY);
			}
		});

		try {
			this.sceneService.getScene("landsat:EXTERNAL_ID", "api-abc-123", false);
			fail("get scene should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.BAD_GATEWAY, ex.getRecommendedStatusCode());
		}
	}
}
