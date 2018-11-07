/**
 * Copyright 2018, Radiant Solutions, Inc.
 * <p>
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * <p>
 * http://www.apache.org/licenses/LICENSE-2.0
 * <p>
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
package org.venice.beachfront.bfapi.geoserver;

import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.Paths;

import javax.annotation.PostConstruct;

import org.apache.http.client.HttpClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.databind.ObjectMapper;

import model.logger.Severity;
import util.PiazzaLogger;

/**
 * Checks the GeoServer Layer, Style during initialization to ensure that they exist before use.
 */
@Component
public class GeoserverEnvironment {
	@Value("${vcap.services.pz-geoserver.credentials.boundless_geoserver_url}")
	private String GEOSERVER_HOST;
	@Value("${geoserver.workspace.name}")
	private String WORKSPACE_NAME;
	@Value("${geoserver.datastore.name}")
	private String DATASTORE_NAME;
	@Value("${geoserver.layer.name}")
	private String LAYER_NAME;
	@Value("${geoserver.layergroup.name}")
	private String LAYER_GROUP_NAME;
	@Value("${geoserver.style.name}")
	private String STYLE_NAME;
	@Value("${geoserver.timeout}")
	private int geoserverTimeout;
	@Value("${exit.on.geoserver.provision.failure}")
	private Boolean exitOnGeoServerProvisionFailure;

	// Class-scoped for mocks. We don't want to autoWire.
	private RestTemplate restTemplate = new RestTemplate();
	@Autowired
	private HttpClient httpClient;
	@Autowired
	private AuthHeaders authHeaders;
	@Autowired
	private ObjectMapper objectMapper;
	@Autowired
	private PiazzaLogger piazzaLogger;

	/**
	 * Invokes initialization logic for Beachfront GeoServer Layer and Style
	 */
	@PostConstruct
	public void initializeEnvironment() {
		piazzaLogger.log("Checking to see if installation of GeoServer Detections Layer and Style is required", Severity.INFORMATIONAL);

		// Since we're on the startup thread, we want to try to complete quickly. e.g. don't wait for slow connections.
		// Configure a reasonable timeout for the rest client to abort slow requests.
		HttpComponentsClientHttpRequestFactory requestFactory = new HttpComponentsClientHttpRequestFactory(this.httpClient);
		requestFactory.setReadTimeout(geoserverTimeout);
		restTemplate.setRequestFactory(requestFactory);

		// Check GeoServer Layer
		{
			// In GeoServer 2.9 layers can't be accessed by workspace, so use the Geoserver base url.
			final String layerURL = String.format("%s/rest/layers/%s:%s.json", getGeoServerBaseUrl(), WORKSPACE_NAME, LAYER_NAME);

			if (!doesResourceExist(layerURL)) {
				piazzaLogger.log("GeoServer Layer does not exist; Attempting creation.", Severity.INFORMATIONAL);
				installLayer();
			} else {
				piazzaLogger.log("GeoServer Layer exists and will not be recreated.", Severity.INFORMATIONAL);
			}
		}

		// Check GeoServer Style
		{
			final String styleURL = String.format("%s/styles/%s.json", getWorkspaceBaseUrl(), STYLE_NAME);

			if (!doesResourceExist(styleURL)) {
				piazzaLogger.log("GeoServer Style does not exist; Attempting creation.", Severity.INFORMATIONAL);
				installStyle();
			} else {
				piazzaLogger.log("GeoServer Style exists and will not be recreated.", Severity.INFORMATIONAL);
			}
		}

		// Check GeoServer LayerGroup
		{
			final String layerGroupURL = String.format("%s/layergroups/%s.json", getWorkspaceBaseUrl(), LAYER_GROUP_NAME);

			if (!doesResourceExist(layerGroupURL)) {
				piazzaLogger.log("GeoServer Layer Group does not exist; Attempting creation.", Severity.INFORMATIONAL);
				installLayerGroup();
			} else {
				piazzaLogger.log("GeoServer Layer Group exists and will not be recreated.", Severity.INFORMATIONAL);
			}
		}
	}

	/**
	 * Checks if a GeoServer resource exists (200 OK returns from the server. 404 indicates not exists) Note:
	 * resourceUri must return valid JSON for the resource to be considered extant.
	 *
	 * @return True if exists, false if not
	 */
	private boolean doesResourceExist(final String resourceUri) {
		// Check if exists
		final HttpEntity<String> request = new HttpEntity<>(authHeaders.get());

		try {
			piazzaLogger.log(String.format("Checking if GeoServer Resource Exists at %s", resourceUri), Severity.INFORMATIONAL);

			final ResponseEntity<String> response = restTemplate.exchange(resourceUri, HttpMethod.GET, request, String.class);

			// Validate that the response body is JSON. Otherwise, an authentication redirect error may have occurred.
			try {
				objectMapper.readTree(response.getBody());
			} catch (final IOException exception) {
				String error = String.format(
						"Received a non-error response from GeoServer resource check for %s, but it was not valid JSON. Authentication may have failed.",
						resourceUri, response.getBody());
				piazzaLogger.log(error, Severity.ERROR);
				return false;
			}

			if (response.getStatusCode().is2xxSuccessful()) {
				return true;
			}
		} catch (final HttpClientErrorException | HttpServerErrorException exception) {
			// If it's a 404, then it does not exist. Fall through.
			if (!exception.getStatusCode().equals(HttpStatus.NOT_FOUND)) {
				// If it's anything but a 404, then it's a server error and we should not proceed with creation. Throw
				// an exception.
				piazzaLogger.log(String.format("HTTP Status Error checking GeoServer Resource %s Exists with message %s", resourceUri,
						exception.getStatusCode().toString()), Severity.ERROR);
			}
		} catch (final RestClientException exception) {
			piazzaLogger.log(String.format("Unexpected Error while checking for GeoServer Resource %s with error %s", resourceUri,
					exception.getMessage()), Severity.ERROR);
		}

		return false;
	}

	private void installLayer() {
		authHeaders.setContentType(MediaType.APPLICATION_XML);
		final String layerURL = String.format("%s/datastores/%s/featuretypes", getWorkspaceBaseUrl(), DATASTORE_NAME);

		try {
			final HttpEntity<String> request = new HttpEntity<>(getLayerCreationPayload(), authHeaders.get());
			restTemplate.exchange(layerURL, HttpMethod.POST, request, String.class);
			piazzaLogger.log("GeoServer Detections Layer created successfully.", Severity.INFORMATIONAL);
		} catch (final HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("HTTP Error occurred while trying to create Beachfront GeoServer Layer: %s",
					exception.getResponseBodyAsString()), Severity.ERROR);
			determineExit();
		} catch (final IOException | URISyntaxException | ResourceAccessException exception) {
			piazzaLogger.log(String.format("Unexpected Error Reading GeoServer Layer XML with message %s", exception.getMessage()),
					Severity.ERROR);
		}
	}

	private void installStyle() {
		authHeaders.setContentType(MediaType.parseMediaType("application/vnd.ogc.sld+xml"));
		final String styleURL = String.format("%s/styles?name=%s", getWorkspaceBaseUrl(), STYLE_NAME);

		try {
			final HttpEntity<String> request = new HttpEntity<>(getStyleCreationPayload(), authHeaders.get());
			restTemplate.exchange(styleURL, HttpMethod.POST, request, String.class);
			piazzaLogger.log("GeoServer Style Layer created successfully.", Severity.INFORMATIONAL);
		} catch (final HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("HTTP Error occurred while trying to create Beachfront GeoServer Style: %s",
					exception.getResponseBodyAsString()), Severity.ERROR);
			determineExit();
		} catch (final IOException | URISyntaxException | ResourceAccessException exception) {
			piazzaLogger.log(String.format("Unexpected Error Reading GeoServer Style XML with message %s", exception.getMessage()),
					Severity.ERROR);
		}
	}

	private void installLayerGroup() {
		authHeaders.setContentType(MediaType.parseMediaType("application/xml"));
		final String layerGroupURL = String.format("%s/layergroups", getWorkspaceBaseUrl());

		try {
			final HttpEntity<String> request = new HttpEntity<>(getLayerGroupCreationPayload(), authHeaders.get());
			restTemplate.exchange(layerGroupURL, HttpMethod.POST, request, String.class);
			piazzaLogger.log("GeoServer Layer Group created successfully.", Severity.INFORMATIONAL);
		} catch (final HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("HTTP Error occurred while trying to create Beachfront GeoServer Layer Group: %s",
					exception.getResponseBodyAsString()), Severity.ERROR);
			determineExit();
		} catch (final IOException | URISyntaxException | ResourceAccessException exception) {
			piazzaLogger.log(String.format("Unexpected Error Reading GeoServer Layer Group XML with message %s", exception.getMessage()),
					Severity.ERROR);
		}
	}

	private String getLayerCreationPayload() throws IOException, URISyntaxException {
		return replaceNameTokens(
				new String(Files.readAllBytes(Paths.get(getClass().getClassLoader().getResource("geoserver/layer_creation.xml").toURI()))));
	}

	private String getStyleCreationPayload() throws IOException, URISyntaxException {
		return replaceNameTokens(
				new String(Files.readAllBytes(Paths.get(getClass().getClassLoader().getResource("geoserver/style_creation.xml").toURI()))));
	}

	private String getLayerGroupCreationPayload() throws IOException, URISyntaxException {
		return replaceNameTokens(new String(
				Files.readAllBytes(Paths.get(getClass().getClassLoader().getResource("geoserver/layer_group_creation.xml").toURI()))));
	}

	private String replaceNameTokens(String original) {
		return original.replaceAll("WORKSPACE_NAME", WORKSPACE_NAME).replaceAll("LAYER_NAME", LAYER_NAME)
				.replaceAll("LAYER_GROUP_NAME", LAYER_GROUP_NAME).replaceAll("DATASTORE_NAME", DATASTORE_NAME)
				.replaceAll("STYLE_NAME", STYLE_NAME);
	}

	/**
	 * Gets the base GeoServer URL.
	 * <p>
	 * The GeoServer URL as reported by On-Demand service tile is something along the lines of:
	 * "https://geoserver.ip/geoserver/index.html". In our requests to GeoServer, the index.html portion of the URL is
	 * obstructing. This method will take in the current VCAP variable for the Boundless URL and return the URL base
	 * (leading up to the /geoserver path) that can be used to construct URLs for proper POST/PUTs to GeoServer.
	 * </p>
	 * <p>
	 * The return value will take on the form of "http://geoserver.ip/geoserver". Protocol will be determined by the
	 * VCAP variable. Port will be included if defined in the VCAP, otherwise it will not be present. There will be no
	 * trailing slash at the end of the URL.
	 * </p>
	 */
	public String getGeoServerBaseUrl() {
		String baseUrl = GEOSERVER_HOST;
		if (GEOSERVER_HOST.contains("/index.html")) {
			baseUrl = GEOSERVER_HOST.replace("/index.html", "");
		}
		return baseUrl;
	}

	public String getWorkspaceBaseUrl() {
		return String.format("%s/rest/workspaces/%s", getGeoServerBaseUrl(), WORKSPACE_NAME);
	}

	/**
	 * If the application is configured to exit on GeoServer configuration error, this method will terminate it.
	 */
	private void determineExit() {
		if (exitOnGeoServerProvisionFailure.booleanValue()) {
			piazzaLogger.log(
					"GeoServer resources could not be appropriately provisioned due to errors received from GeoServer. This application is configured to shut down and will do so now.",
					Severity.INFORMATIONAL);
			System.exit(1);
		}
	}
}