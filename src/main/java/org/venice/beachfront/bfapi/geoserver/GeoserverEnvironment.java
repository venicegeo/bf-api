/**
 * Copyright 2016, RadiantBlue Technologies, Inc.
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

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * Checks the GeoServer Layer, Style during initialization to ensure that they exist before use.
 * 
 * @author Russell.Orf
 *
 */
@Component
public class GeoserverEnvironment {

	private static final Logger LOG = LoggerFactory.getLogger(GeoserverEnvironment.class);

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

	/**
	 * Invokes initialization logic for Beachfront GeoServer Layer and Style
	 */
	@PostConstruct
	public void initializeEnvironment() {

		LOG.info("Checking to see if installation of GeoServer Style, Layer is required");

		// Check GeoServer Layer
		{
			final String layerURL = String.format("%s/rest/layers/%s", getGeoServerBaseUrl(), LAYER_NAME);

			if( !doesResourceExist(layerURL) ) {
				LOG.info("GeoServer Layer does not exist; Attempting creation...");
				installLayer();
			}
			else {
				LOG.info("GeoServer Layer exists and will not be reinstalled.");
			}
		}

		// Check GeoServer Style
		{
			final String styleURL = String.format("%s/rest/styles/%s", getGeoServerBaseUrl(), STYLE_NAME);

			if( !doesResourceExist(styleURL) ) {
				LOG.info("GeoServer Style does not exist; Attempting creation...");
				installStyle();
			}
			else {
				LOG.info("GeoServer Style exists and will not be reinstalled.");
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
			LOG.info("Checking if GeoServer Resource Exists at {}", resourceUri);

			final ResponseEntity<String> response = restTemplate.exchange(resourceUri, HttpMethod.GET, request, String.class);

			// Validate that the response body is JSON. Otherwise, an authentication redirect error may have occurred.
			try {
				objectMapper.readTree(response.getBody());
			} 
			catch (final IOException exception) {
				String error = String.format(
						"Received a non-error response from GeoServer resource check for %s, but it was not valid JSON. Authentication may have failed. ",
						resourceUri, response.getBody());
				LOG.error(error, exception);

				return false;
			}

			if (response.getStatusCode().is2xxSuccessful()) {
				return true;
			}
		} 
		catch (final HttpClientErrorException | HttpServerErrorException exception) {
			// If it's a 404, then it does not exist. Fall through.
			if (!exception.getStatusCode().equals(HttpStatus.NOT_FOUND)) {
				// If it's anything but a 404, then it's a server error and we should not proceed with creation. Throw
				// an exception.
				LOG.error("HTTP Status Error checking GeoServer Resource {} Exists : {}" + resourceUri,
						exception.getStatusCode().toString(), exception);
			}
		} 
		catch (final RestClientException exception) {
			LOG.error("Unexpected Error Checking GeoServer Resource Exists : " + resourceUri, exception);
		}

		return false;
	}

	private void installLayer() {

		authHeaders.setContentType(MediaType.APPLICATION_XML);
		final String layerURL = String.format("%s/rest/workspaces/%s/datastores/%s/featuretypes", getGeoServerBaseUrl(), WORKSPACE_NAME, DATASTORE_NAME);

		try {
			final HttpEntity<String> request = new HttpEntity<>(getLayerCreationPayload(), authHeaders.get());
			restTemplate.exchange(layerURL, HttpMethod.POST, request, String.class);

			LOG.info("GeoServer Layer created successfully!");
		}
		catch (final HttpClientErrorException | HttpServerErrorException exception) {
			final String error = String.format("HTTP Error occurred while trying to create Beachfront GeoServer Layer: %s",
					exception.getResponseBodyAsString());
			LOG.error(error, exception);
		}
		catch (final RestClientException exception) {
			LOG.error("Unexpected Error Creating GeoServer Layer!", exception);
		}
		catch (final IOException | URISyntaxException exception) {
			LOG.error("Unexpected Error Reading GeoServer Layer XML!", exception);
		}
	}

	private void installStyle() {

		authHeaders.setContentType(MediaType.parseMediaType("application/vnd.ogc.sld+xml"));
		final String styleURL = String.format("%s/rest/styles?name=%s", getGeoServerBaseUrl(), STYLE_NAME);

		try {
			final HttpEntity<String> request = new HttpEntity<>(getStyleCreationPayload(), authHeaders.get());
			restTemplate.exchange(styleURL, HttpMethod.POST, request, String.class);

			LOG.info("GeoServer Style created successfully!");
		}
		catch (final HttpClientErrorException | HttpServerErrorException exception) {
			final String error = String.format("HTTP Error occurred while trying to create Beachfront GeoServer Style: %s",
					exception.getResponseBodyAsString());
			LOG.error(error, exception);
		} 
		catch (final RestClientException exception) {
			LOG.error("Unexpected Error Creating GeoServer Style!", exception);
		}
		catch (final IOException | URISyntaxException exception) {
			LOG.error("Unexpected Error Reading GeoServer Layer XML!", exception);
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