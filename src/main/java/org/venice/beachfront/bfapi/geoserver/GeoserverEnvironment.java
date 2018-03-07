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
package org.venice.beachfront.bfapi.geoserver;

import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.Paths;

import javax.annotation.PostConstruct;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
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
 * 
 * @author Russell.Orf
 *
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
	@Value("${geoserver.style.name}")
	private String STYLE_NAME;

	@Autowired
	private RestTemplate restTemplate;
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

		// Check GeoServer Layer
		{
			final String layerURL = String.format("%s/rest/layers/%s", getGeoServerBaseUrl(), LAYER_NAME);

			if (!doesResourceExist(layerURL)) {
				piazzaLogger.log("GeoServer Layer does not exist; Attempting creation.", Severity.INFORMATIONAL);
				installLayer();
			} else {
				piazzaLogger.log("GeoServer Layer exists and will not be recreated.", Severity.INFORMATIONAL);
			}
		}

		// Check GeoServer Style
		{
			final String styleURL = String.format("%s/rest/styles/%s", getGeoServerBaseUrl(), STYLE_NAME);

			if (!doesResourceExist(styleURL)) {
				piazzaLogger.log("GeoServer Style does not exist; Attempting creation.", Severity.INFORMATIONAL);
				installStyle();
			} else {
				piazzaLogger.log("GeoServer Style exists and will not be recreated.", Severity.INFORMATIONAL);
			}
		}
	}

	/**
	 * Checks if a GeoServer resource exists (200 OK returns from the server. 404 indicates not exists)
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
		final String layerURL = String.format("%s/rest/workspaces/%s/datastores/%s/featuretypes", getGeoServerBaseUrl(), WORKSPACE_NAME,
				DATASTORE_NAME);

		try {
			final HttpEntity<String> request = new HttpEntity<>(getLayerCreationPayload(), authHeaders.get());
			restTemplate.exchange(layerURL, HttpMethod.POST, request, String.class);
			piazzaLogger.log("GeoServer Detections Layer created successfully.", Severity.INFORMATIONAL);
		} catch (final HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("HTTP Error occurred while trying to create Beachfront GeoServer Layer: %s",
					exception.getResponseBodyAsString()), Severity.ERROR);
		} catch (final IOException | URISyntaxException | ResourceAccessException exception) {
			piazzaLogger.log(String.format("Unexpected Error Reading GeoServer Layer XML with message %s", exception.getMessage()),
					Severity.ERROR);
		}
	}

	private void installStyle() {
		authHeaders.setContentType(MediaType.parseMediaType("application/vnd.ogc.sld+xml"));
		final String styleURL = String.format("%s/rest/styles?name=%s", getGeoServerBaseUrl(), STYLE_NAME);

		try {
			final HttpEntity<String> request = new HttpEntity<>(getStyleCreationPayload(), authHeaders.get());
			restTemplate.exchange(styleURL, HttpMethod.POST, request, String.class);
			piazzaLogger.log("GeoServer Style Layer created successfully.", Severity.INFORMATIONAL);
		} catch (final HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("HTTP Error occurred while trying to create Beachfront GeoServer Style: %s",
					exception.getResponseBodyAsString()), Severity.ERROR);
		} catch (final IOException | URISyntaxException | ResourceAccessException exception) {
			piazzaLogger.log(String.format("Unexpected Error Reading GeoServer Style XML with message %s", exception.getMessage()),
					Severity.ERROR);
		}
	}

	private String getLayerCreationPayload() throws IOException, URISyntaxException {
		return new String(Files.readAllBytes(Paths.get(getClass().getClassLoader().getResource("geoserver/layer_creation.xml").toURI())))
				.replaceAll("LAYER_NAME", LAYER_NAME);
	}

	private String getStyleCreationPayload() throws IOException, URISyntaxException {
		return new String(Files.readAllBytes(Paths.get(getClass().getClassLoader().getResource("geoserver/style_creation.xml").toURI())));
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
}