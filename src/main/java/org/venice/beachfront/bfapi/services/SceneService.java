package org.venice.beachfront.bfapi.services;

import java.net.URI;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;

import com.fasterxml.jackson.databind.JsonNode;

@Service
public class SceneService {
	@Value("${ia.broker.activation-poll-interval-sec}")
	private int asyncActivationPollIntervalSeconds;
	
	@Value("${ia.broker.activation-poll-max-attempts}")
	private int asyncActivationPollMaxAttempts;

	@Autowired
	private RestTemplate restTemplate;

	@Autowired
	private ExecutorService executor;

	@Value("${ia.broker.protocol}")
	private String iaBrokerProtocol;

	@Value("${ia.broker.server")
	private String iaBrokerServer;

	@Value("${ia.broker.port}")
	private int iaBrokerPort;
	
	@Value("${DOMAIN}")
	private String bfDomain;

	public void activateScene(Scene scene, String planetApiKey) throws UserException {
		if (!scene.getStatus().equals(Scene.STATUS_INACTIVE)) {
			return;
		}

		String platform = Scene.parsePlatform(scene.getSceneId());

		String activationPath = String.format("planet/activate/%s/%s", platform, scene.getExternalId());

		ResponseEntity<String> response;
		try {
			response = this.restTemplate.getForEntity(
					UriComponentsBuilder.newInstance().scheme(this.iaBrokerProtocol).host(this.iaBrokerServer).port(this.iaBrokerPort)
							.path(activationPath).queryParam("PLANET_API_KEY", planetApiKey).build().toUri(),
					String.class);
		} catch (RestClientException ex) {
			String details = String.format("path=%s", activationPath);
			throw new UserException("Unknown exception while querying broker", ex, details, HttpStatus.INTERNAL_SERVER_ERROR);
		}

		if (!response.getStatusCode().is2xxSuccessful()) {
			switch (response.getStatusCodeValue()) {
			case 401:
				throw new UserException("Broker returned 401: Unauthorized", HttpStatus.UNAUTHORIZED);
			case 404:
				throw new UserException("Scene not found", HttpStatus.NOT_FOUND);
			default:
				String simpleMessage = String.format("Received non-OK status %d from broker", response.getStatusCodeValue());
				throw new UserException(simpleMessage, response.getBody() , HttpStatus.BAD_GATEWAY);
			}
		}
	}

	public Scene getScene(String sceneId, String planetApiKey, boolean withTides) throws UserException {
		String platform = Scene.parsePlatform(sceneId);
		String externalId = Scene.parseExternalId(sceneId);

		String scenePath = String.format("planet/%s/%s", platform, externalId);

		ResponseEntity<JsonNode> response;
		try {
			response = this.restTemplate.getForEntity(
				UriComponentsBuilder.newInstance().scheme(this.iaBrokerProtocol).host(this.iaBrokerServer).port(this.iaBrokerPort)
						.path(scenePath).queryParam("PLANET_API_KEY", planetApiKey).queryParam("tides", withTides).build().toUri(),
						JsonNode.class);
		} catch (RestClientException ex) {
			String details = String.format("path=%s", scenePath);
			throw new UserException("Unknown exception while querying broker", ex, details, HttpStatus.INTERNAL_SERVER_ERROR);
		}
			
		if (!response.getStatusCode().is2xxSuccessful()) {
			switch (response.getStatusCodeValue()) {
			case 401:
				throw new UserException("Broker returned 401: Unauthorized", HttpStatus.UNAUTHORIZED);
			case 404:
				throw new UserException("Scene not found", HttpStatus.NOT_FOUND);
			case 502:
				throw new UserException("Upstream broker error", response.getBody().toString(), HttpStatus.BAD_GATEWAY);
			default:
				String simpleMessage = String.format("Received non-OK status %d from broker", response.getStatusCodeValue());
				throw new UserException(simpleMessage, response.getBody().toString(), HttpStatus.BAD_GATEWAY);			}
		}
		
		JsonNode responseJson = response.getBody();

		Scene scene = new Scene();
		try {
			scene.setRawJson(responseJson);
			scene.setSceneId(responseJson.get("id").asText());
			scene.setCloudCover(responseJson.get("properties").get("cloudCover").asDouble());
			scene.setResolution(responseJson.get("properties").get("resolution").asInt());
			scene.setCaptureTime(DateTime.parse(responseJson.get("properties").get("acquiredDate").asText()));
			scene.setSensorName(responseJson.get("properties").get("sensorName").asText());
			scene.setUri(responseJson.get("properties").get("location").asText());
	
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
			throw new UserException("Error parsing JSON response from upstream", ex, HttpStatus.INTERNAL_SERVER_ERROR);
		}

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
			}

			try {
				Thread.sleep(asyncActivationPollIntervalSeconds * 1000);
			} catch (InterruptedException e) {
				throw new RuntimeException(e);
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
		return UriComponentsBuilder.newInstance()
				.scheme("https")
				.host("bf-api." + bfDomain)
				.pathSegment("scene", scene.getSceneId(), "download")
				.queryParam("planet_api_key", planetApiKey)
				.build()
				.toUri();
	}

}
