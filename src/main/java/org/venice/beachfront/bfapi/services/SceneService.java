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

import java.io.IOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;

import org.geotools.geojson.feature.FeatureJSON;
import org.joda.time.DateTime;
import org.opengis.feature.simple.SimpleFeature;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import org.venice.beachfront.bfapi.database.dao.SceneDao;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.vividsolutions.jts.geom.Geometry;

import model.logger.Severity;
import util.PiazzaLogger;

@Service
public class SceneService {
	@Value("${ia.broker.activation-poll-interval-sec}")
	private int asyncActivationPollIntervalSeconds;
	@Value("${ia.broker.activation-poll-max-attempts}")
	private int asyncActivationPollMaxAttempts;
	@Value("${ia.broker.protocol}")
	private String iaBrokerProtocol;
	@Value("${ia.broker.server}")
	private String iaBrokerServer;
	@Value("${ia.broker.port}")
	private int iaBrokerPort;
	@Value("${DOMAIN}")
	private String bfDomain;

	@Autowired
	private RestTemplate restTemplate;
	@Autowired
	private ExecutorService executor;
	@Autowired
	private PiazzaLogger piazzaLogger;
	@Autowired
	private SceneDao sceneDao;

	public void activateScene(Scene scene, String planetApiKey) throws UserException {
		if (!scene.getStatus().equals(Scene.STATUS_INACTIVE)) {
			piazzaLogger.log(String.format("Scene %s was not inactive. No need to reactivate.", scene.getSceneId()),
					Severity.INFORMATIONAL);
			return;
		}

		String platform = Scene.parsePlatform(scene.getSceneId());
		String activationPath = String.format("planet/activate/%s/%s", platform, scene.getExternalId());

		try {
			this.restTemplate.getForEntity(UriComponentsBuilder.newInstance().scheme(this.iaBrokerProtocol).host(this.iaBrokerServer)
					.port(this.iaBrokerPort).path(activationPath).queryParam("PL_API_KEY", planetApiKey).build().toUri(), Object.class);
			piazzaLogger.log(String.format("Successfully requested Activation of Scene %s to URL %s", scene.getSceneId(), activationPath),
					Severity.INFORMATIONAL);
		} catch (HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("Error activating Scene %s with Code %s and Message %s", scene.getSceneId(),
					exception.getRawStatusCode(), exception.getResponseBodyAsString()), Severity.ERROR);
			
			HttpStatus recommendedErrorStatus = exception.getStatusCode();
			if (recommendedErrorStatus.equals(HttpStatus.UNAUTHORIZED)) {
			  recommendedErrorStatus = HttpStatus.BAD_REQUEST; // 401 Unauthorized logs out the client, and we don't want that
			}

			String message = String.format("Upstream error activating Planet scene. (%d) platform=%s id=%s", exception.getStatusCode().value(), platform, scene.getExternalId());
			throw new UserException(message, exception.getMessage(), recommendedErrorStatus);
		}
	}

	/**
	 * Gets the Scene object from the local scene database. This does not reach out to the IA-broker, but rather, the
	 * Beachfront database.
	 * <p>
	 * The Scenes get written to this database as they are requested through Planet. If a Scene ID is requested for a
	 * valid scene that has not been queried through planet, then that scene will not be present in the database.
	 * <p>
	 * The purpose of this function is to return scene geometries immediately through the database for fast and large
	 * lookups of Job geometries, without having to broker each request back through the IA-Broker.
	 * 
	 * @param sceneId
	 * @return
	 */
	public Scene getSceneFromLocalDatabase(String sceneId) {
		return sceneDao.findBySceneId(sceneId);
	}

	/**
	 * Gets Scene information from the IA-broker.
	 * <p>
	 * As part of this process, the Scene metadata will be written to the local Beachfront database.
	 * 
	 * @param sceneId
	 *            The scene ID
	 * @param planetApiKey
	 *            The users planet key
	 * @param withTides
	 *            Include tides information or not
	 * @return The Scene object
	 */
	public Scene getScene(String sceneId, String planetApiKey, boolean withTides) throws UserException {
		piazzaLogger.log(String.format("Requesting Scene %s information.", sceneId), Severity.INFORMATIONAL);
		String platform = Scene.parsePlatform(sceneId);
		String externalId = Scene.parseExternalId(sceneId);

		String scenePath = String.format("planet/%s/%s", platform, externalId);

		ResponseEntity<JsonNode> response;
		try {
			response = this.restTemplate.getForEntity(
					UriComponentsBuilder.newInstance().scheme(this.iaBrokerProtocol).host(this.iaBrokerServer).port(this.iaBrokerPort)
							.path(scenePath).queryParam("PL_API_KEY", planetApiKey).queryParam("tides", withTides).build().toUri(),
					JsonNode.class);
		} catch (HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("Error Requesting Information for Scene %s with Code %s and Message %s", sceneId,
					exception.getRawStatusCode(), exception.getResponseBodyAsString()), Severity.ERROR);
			
			HttpStatus recommendedErrorStatus = exception.getStatusCode();
			if (recommendedErrorStatus.equals(HttpStatus.UNAUTHORIZED)) {
			  recommendedErrorStatus = HttpStatus.BAD_REQUEST; // 401 Unauthorized logs out the client, and we don't want that
			}

			String message = String.format("Upstream error getting Planet scene. (%d) platform=%s id=%s", exception.getStatusCode().value(), platform, externalId);
			throw new UserException(message, exception.getMessage(), recommendedErrorStatus);
		}

		JsonNode responseJson = response.getBody();

		Scene scene = new Scene();
		try {
			piazzaLogger.log(String.format("Beginning parsing of successful response of Scene %s data.", sceneId),
					Severity.INFORMATIONAL);
			scene.setRawJson(responseJson);
			scene.setSceneId(platform + ":" + responseJson.get("id").asText());
			scene.setCloudCover(responseJson.get("properties").get("cloudCover").asDouble());
			scene.setResolution(responseJson.get("properties").get("resolution").asInt());
			scene.setCaptureTime(DateTime.parse(responseJson.get("properties").get("acquiredDate").asText()));
			scene.setSensorName(responseJson.get("properties").get("sensorName").asText());
			scene.setUri(UriComponentsBuilder.newInstance().scheme(this.iaBrokerProtocol).host(this.iaBrokerServer).port(this.iaBrokerPort)
							.path(scenePath).toUriString());

			try {
				// The response from IA-Broker is a GeoJSON feature. Convert to Geometry.
				FeatureJSON featureReader = new FeatureJSON();
				String geoJsonString = new ObjectMapper().writeValueAsString(responseJson);
				SimpleFeature feature = featureReader.readFeature(geoJsonString);
				Geometry geometry = (Geometry) feature.getDefaultGeometry();
				scene.setGeometry(geometry);
			} catch (IOException exception) {
				String error = String.format(
						"Could not convert Scene %s response to GeoJSON object. This scene will not store properly in the database.",
						scene.getSceneId());
				piazzaLogger.log(error, Severity.ERROR);
				throw new UserException(error, exception, HttpStatus.INTERNAL_SERVER_ERROR);
			}

			String status = "active";
			if (platform.equals(Scene.PLATFORM_RAPIDEYE) || platform.equals(Scene.PLATFORM_PLANETSCOPE)) {
				status = responseJson.get("properties").get("status").asText();
			} else {
				// Status active
			}

			scene.setStatus(status);

			if (withTides) {
				scene.setTide(responseJson.get("properties").get("CurrentTide").asDouble());
				scene.setTideMin24H(responseJson.get("properties").get("MinimumTide24Hours").asDouble());
				scene.setTideMax24H(responseJson.get("properties").get("MaximumTide24Hours").asDouble());
			}
		} catch (NullPointerException ex) {
			piazzaLogger.log(String.format(
					"Error parsing of successful response from IA-Broker for Scene %s data with Error %s. Raw Response content: %s",
					sceneId, ex.getMessage(), responseJson.toString()), Severity.ERROR);
			throw new UserException("Error parsing JSON Scene Response from Upstream Broker Service.", ex,
					HttpStatus.INTERNAL_SERVER_ERROR);
		}

		piazzaLogger.log(String.format("Successfully parsed Scene metadata for Scene %s", sceneId), Severity.INFORMATIONAL);
		sceneDao.save(scene);
		return scene;
	}

	public CompletableFuture<Scene> asyncGetActiveScene(String sceneId, String planetApiKey, boolean withTides) {
		return CompletableFuture.supplyAsync(() -> {
			for (int i = 0; i < asyncActivationPollMaxAttempts; i++) {
				Scene updatedScene;

				try {
					updatedScene = this.getScene(sceneId, planetApiKey, withTides);
				} catch (UserException e) {
					throw new RuntimeException(e);
				}

				if (updatedScene.getStatus().equals(Scene.STATUS_ACTIVE)) {
					return updatedScene;
				}

				try {
					Thread.sleep(asyncActivationPollIntervalSeconds * 1000L);
				} catch (Exception e) {
					throw new RuntimeException(e);
				}
			}

			throw new RuntimeException(new UserException("Upstream server timed out", HttpStatus.GATEWAY_TIMEOUT));
		}, this.executor);
	}

	/**
	 * Gets the download URI for the specified scene
	 * 
	 * @param scene
	 * @param planetApiKey
	 * @return
	 */
	public URI getDownloadUri(Scene scene, String planetApiKey) {
		// https://bf-api.{domain}/scene/{id}/download?planet_api_key={key}
		return UriComponentsBuilder.newInstance().scheme("https").host("bf-api." + bfDomain)
				.pathSegment("scene", scene.getSceneId(), "download").queryParam("planet_api_key", planetApiKey).build().toUri();
	}

	public List<String> getSceneInputFileNames(Scene scene) {
		switch (Scene.parsePlatform(scene.getSceneId())) {
		case Scene.PLATFORM_RAPIDEYE:
		case Scene.PLATFORM_PLANETSCOPE:
			return Arrays.asList("multispectral.TIF");
		case Scene.PLATFORM_LANDSAT:
			return Arrays.asList("coastal.TIF", "swir1.TIF");
		case Scene.PLATFORM_SENTINEL:
			return Arrays.asList("coastal.JP2", "swir1.JP2");
		}
		return new ArrayList<>();
	}

	public List<String> getSceneInputURLs(Scene scene) {
		switch (Scene.parsePlatform(scene.getSceneId())) {
		case Scene.PLATFORM_RAPIDEYE:
		case Scene.PLATFORM_PLANETSCOPE:
			return Arrays.asList(scene.getLocationProperty());
		case Scene.PLATFORM_LANDSAT:
			return Arrays.asList(scene.getImageBand("coastal"), scene.getImageBand("swir1"));
		case Scene.PLATFORM_SENTINEL:
			return Arrays.asList(scene.getImageBand("blue"), scene.getImageBand("nir"));
		}
		return new ArrayList<>();
	}

}
