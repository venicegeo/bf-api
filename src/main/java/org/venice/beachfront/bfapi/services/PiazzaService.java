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
import java.net.URI;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.io.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.piazza.StatusMetadata;
import org.venice.beachfront.bfapi.services.converter.ShapefileConverter;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import model.logger.Severity;
import util.PiazzaLogger;

@Service
public class PiazzaService {
	@Value("${piazza.server}")
	private String PIAZZA_URL;
	@Value("${PIAZZA_API_KEY}")
	private String PIAZZA_API_KEY;

	@Autowired
	private RestTemplate restTemplate;
	@Autowired
	private ObjectMapper objectMapper;
	@Autowired
	private PiazzaLogger piazzaLogger;

	/**
	 * Executes the service, sending the payload to Piazza and parsing the response for the Job ID
	 * 
	 * @param serviceId
	 *            The ID of the Piazza Service corresponding to the chosen algorithm
	 * @param cliCommand
	 *            The algorithm CLI parameters
	 * @param fileNames
	 *            The ordered list of file names
	 * @param fileUrls
	 *            The ordered list of file URLs
	 * @param userId
	 *            The ID of the creating user for this job
	 * @return The Piazza Job ID
	 * @throws Exception
	 */
	public String execute(String serviceId, String cliCommand, List<String> fileNames, List<String> fileUrls, String userId)
			throws UserException {
		String piazzaJobUrl = String.format("%s/job", PIAZZA_URL);
		piazzaLogger
				.log(String.format("Preparing to submit Execute Job request to Piazza at %s to Service ID %s by User %s with Command %s.",
						piazzaJobUrl, serviceId, userId, cliCommand), Severity.INFORMATIONAL);
		HttpHeaders headers = createPiazzaHeaders(PIAZZA_API_KEY);
		// Structure the Job Request
		String requestJson = null;
		try {
			// Add quotations to each element in the files lists, to ensure that JSON has the quotes after the
			// string-replace.
			List<String> quotedFileNames = new ArrayList<String>();
			List<String> quotedFileUrls = new ArrayList<String>();
			for (String fileName : fileNames) {
				quotedFileNames.add(String.format("\\\"%s\\\"", fileName));
			}
			for (String fileUrl : fileUrls) {
				quotedFileUrls.add(String.format("\\\"%s\\\"", fileUrl));
			}
			// Replace all user values into the execute request JSON template
			requestJson = String.format(loadJobRequestJson(), serviceId, cliCommand, String.join(", ", quotedFileUrls),
					String.join(", ", quotedFileNames), userId);
		} catch (Exception exception) {
			exception.printStackTrace();
			throw new UserException("Could not load local resource file for Job Request.", exception.getMessage(),
					HttpStatus.INTERNAL_SERVER_ERROR);
		}
		HttpEntity<String> request = new HttpEntity<>(requestJson, headers);

		// Execute the Request
		ResponseEntity<String> response = null;
		try {
			response = restTemplate.exchange(URI.create(piazzaJobUrl), HttpMethod.POST, request, String.class);
		} catch (HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(
					String.format("Piazza Job Request by User %s has failed with Code %s and Error %s. The body of the request was: %s",
							userId, exception.getStatusText(), exception.getResponseBodyAsString(), requestJson),
					Severity.ERROR);
			throw new UserException("There was an error submitting the Job Request to Piazza.", exception.getMessage(),
					exception.getStatusCode());
		}

		// Ensure the response succeeded
		if (!response.getStatusCode().is2xxSuccessful()) {
			// Error occurred - report back to the user
			throw new UserException("Piazza returned a non-OK status code when submitting the Job.", response.getStatusCode().toString(),
					response.getStatusCode());
		}

		// Parse the Job ID from the response and return
		try {
			JsonNode responseJson = objectMapper.readTree(response.getBody());
			String jobId = responseJson.get("data").get("jobId").asText();
			piazzaLogger.log(String.format("Received successful response from Piazza for Job %s by User %s.", jobId, userId),
					Severity.INFORMATIONAL);
			return jobId;
		} catch (IOException exception) {
			piazzaLogger.log(String.format("Error parsing the successful Piazza Job Response by User %s with Error %s", userId,
					exception.getMessage()), Severity.ERROR);
			throw new UserException("There was an error parsing the Piazza response when submitting the Job.", exception.getMessage(),
					HttpStatus.INTERNAL_SERVER_ERROR);
		}
	}

	/**
	 * Gets the status of the Piazza Job with the specified Job ID
	 * 
	 * @param jobId
	 *            The Job ID
	 * @return The status of the Job, as returned by Piazza
	 */
	public StatusMetadata getJobStatus(String jobId) throws UserException {
		String piazzaJobUrl = String.format("%s/job/%s", PIAZZA_URL, jobId);
		piazzaLogger.log(String.format("Checking Piazza Job Status for Job %s", jobId), Severity.INFORMATIONAL);
		HttpHeaders headers = createPiazzaHeaders(PIAZZA_API_KEY);
		HttpEntity<String> request = new HttpEntity<>(headers);

		// Execute the Request
		ResponseEntity<String> response = null;
		try {
			response = restTemplate.exchange(URI.create(piazzaJobUrl), HttpMethod.GET, request, String.class);
		} catch (HttpClientErrorException | HttpServerErrorException exception) {
			String error = String.format("There was an error fetching Job %s Status from Piazza.", jobId);
			piazzaLogger.log(error, Severity.ERROR);
			throw new UserException(error, exception.getMessage(), exception.getStatusCode());
		}

		// Ensure the response succeeded
		if (!response.getStatusCode().is2xxSuccessful()) {
			// Error occurred - report back to the user
			throw new UserException(String.format("Piazza returned a non-OK status when requesting Job %s Status.", jobId),
					response.getStatusCode().toString(), response.getStatusCode());
		}

		// Parse out the Status from the Response
		try {
			JsonNode responseJson = objectMapper.readTree(response.getBody());
			StatusMetadata status = new StatusMetadata(responseJson.get("data").get("status").asText());
			// Parse additional information depending on status
			if (status.isStatusSuccess()) {
				// If the status is complete, attach the Data ID of the shoreline detection
				status.setDataId(responseJson.get("data").get("result").get("dataId").asText());
			} else if (status.isStatusError()) {
				// If the status is errored, then attach the error information
				status.setErrorMessage(responseJson.get("data").get("message").asText());
			}
			return status;
		} catch (IOException exception) {
			String error = String.format("There was an error parsing the Piazza response when Requesting Job %s Status.", jobId);
			piazzaLogger.log(error, Severity.ERROR);
			throw new UserException(error, exception.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
		}
	}

	/**
	 * Returns the list of all algorithm services that have been registed with the Beachfront Piazza API Key
	 * 
	 * @return List of algorithms available for use in Beachfront
	 */
	public List<Algorithm> getRegisteredAlgorithms() throws UserException {
		String piazzaServicesUrl = String.format("%s/service/me", PIAZZA_URL);
		piazzaLogger.log("Checking Piazza Registered Algorithms.", Severity.INFORMATIONAL);
		HttpHeaders headers = createPiazzaHeaders(PIAZZA_API_KEY);
		HttpEntity<String> request = new HttpEntity<>(headers);

		// Execute the Request
		ResponseEntity<String> response = null;
		try {
			response = restTemplate.exchange(URI.create(piazzaServicesUrl), HttpMethod.GET, request, String.class);
		} catch (HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("Error fetching Algorithms from Piazza with Code %s, Response was %s", exception.getStatusText(),
					exception.getResponseBodyAsString()), Severity.ERROR);
			throw new UserException("There was an error fetching Algorithm List from Piazza.", exception.getMessage(),
					exception.getStatusCode());
		}

		// Ensure the response succeeded
		if (!response.getStatusCode().is2xxSuccessful()) {
			// Error occurred - report back to the user
			throw new UserException("Piazza returned a non-OK status when requesting registered Algorithm List.",
					response.getStatusCode().toString(), response.getStatusCode());
		}

		// Parse out the Algorithms from the Response
		try {
			JsonNode responseJson = objectMapper.readTree(response.getBody());
			JsonNode algorithmJsonArray = responseJson.get("data");
			List<Algorithm> algorithms = new ArrayList<Algorithm>();
			for (JsonNode algorithmJson : algorithmJsonArray) {
				// For each Registered Service, wrap it in the Algorithm Object and add to the list
				algorithms.add(getAlgorithmFromServiceNode(algorithmJson));
			}
			piazzaLogger.log(String.format("Returning full Piazza algorithm list. Found %s Algorithms.", algorithms.size()),
					Severity.INFORMATIONAL);
			return algorithms;
		} catch (IOException exception) {
			String error = "There was an error parsing the Piazza response when Requesting registered Algorithm List.";
			piazzaLogger.log(error, Severity.ERROR);
			throw new UserException(error, exception.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
		}
	}

	/**
	 * Gets the registered algorithm from Piazza based on the Service ID. This can return services that are not owned by
	 * the currently configured Piazza API Key
	 * 
	 * @param serviceId
	 *            Service ID to fetch
	 * @return The Service
	 */
	public Algorithm getRegisteredAlgorithm(String serviceId) throws UserException {
		String piazzaServiceUrl = String.format("%s/service/%s", PIAZZA_URL, serviceId);
		piazzaLogger.log(String.format("Checking Piazza Registered Algorithm %s.", serviceId), Severity.INFORMATIONAL);
		HttpHeaders headers = createPiazzaHeaders(PIAZZA_API_KEY);
		HttpEntity<String> request = new HttpEntity<>(headers);

		// Execute the Request
		ResponseEntity<String> response = null;
		try {
			response = restTemplate.exchange(URI.create(piazzaServiceUrl), HttpMethod.GET, request, String.class);
		} catch (HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("Error fetching Algorithm %s from Piazza with Code %s, Response was %s", serviceId,
					exception.getStatusText(), exception.getResponseBodyAsString()), Severity.ERROR);
			throw new UserException(String.format("There was an error fetching Algorithm %s from Piazza.", serviceId),
					exception.getMessage(), exception.getStatusCode());
		}

		// Ensure the response succeeded
		if (!response.getStatusCode().is2xxSuccessful()) {
			// Error occurred - report back to the user
			throw new UserException(String.format("Piazza returned a non-OK status when requesting registered Algorithm %s.", serviceId),
					response.getStatusCode().toString(), response.getStatusCode());
		}

		// Parse out the Algorithms from the Response
		try {
			JsonNode responseJson = objectMapper.readTree(response.getBody());
			JsonNode algorithmJson = responseJson.get("data");
			return getAlgorithmFromServiceNode(algorithmJson);
		} catch (IOException exception) {
			String error = String.format("There was an error parsing the Piazza response when Requesting registered Algorithm %s.",
					serviceId);
			piazzaLogger.log(error, Severity.ERROR);
			throw new UserException(error, exception.getMessage(), HttpStatus.INTERNAL_SERVER_ERROR);
		}
	}

	/**
	 * Calls the data/file endpoint to download the shoreline detection data from Piazza for the specified Data ID.
	 * These bytes are the raw GeoJSON of the shoreline detection vectors.
	 * 
	 * @param dataId
	 *            Data ID
	 * @return The bytes of the ingested data
	 */
	public byte[] downloadData(String dataId) throws UserException {
		String piazzaDataUrl = String.format("%s/file/%s", PIAZZA_URL, dataId);
		piazzaLogger.log(String.format("Requesting data %s bytes from Piazza at %s", dataId, piazzaDataUrl), Severity.INFORMATIONAL);
		HttpHeaders headers = createPiazzaHeaders(PIAZZA_API_KEY);
		HttpEntity<String> request = new HttpEntity<>(headers);

		// Execute the Request
		ResponseEntity<byte[]> response = null;
		try {
			response = restTemplate.exchange(URI.create(piazzaDataUrl), HttpMethod.GET, request, byte[].class);
		} catch (HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("Error downloading Data Bytes for Data %s from Piazza. Failed with Code %s and Body %s", dataId,
					exception.getStatusText(), exception.getResponseBodyAsString()), Severity.ERROR);
			throw new UserException(String.format("There was an error fetching Data bytes %s from Piazza.", dataId), exception.getMessage(),
					exception.getStatusCode());
		}

		// Ensure the response succeeded
		if (!response.getStatusCode().is2xxSuccessful()) {
			// Error occurred - report back to the user
			throw new UserException(String.format("Piazza returned a non-OK status when requesting Data bytes %s.", dataId),
					response.getStatusCode().toString(), response.getStatusCode());
		}

		byte[] data = response.getBody();
		piazzaLogger.log(String.format("Successfully retrieved Bytes for Data %s from Piazza. File size was %s", dataId, data.length),
				Severity.INFORMATIONAL);
		return data;
	}

	/**
	 * After calling downloadData, converts the GeoJSON to Shapefile
	 * These bytes are the raw zipfile containing the Shapefile of the 
	 * shoreline detection vectors.
	 * 
	 * @param dataId
	 *            Data ID
	 * @return The bytes of the ingested data, as a .zip file containing a Shapefile
	 */
	public byte[] downloadDataAsShapefile(String dataId) throws UserException {
		
		byte[] gjBytes = downloadData(dataId);
		piazzaLogger.log(String.format("Converting data %s to Shapefile", dataId), Severity.INFORMATIONAL);
		ShapefileConverter sfc = new ShapefileConverter();
		final byte[] shapefileBytes = sfc.apply(gjBytes);
		return shapefileBytes;
	}

	/**
	 * Downloads the data for a successful Beachfront Detection Service Job's Metadata..
	 * <p>
	 * The Data will be textual data containing all of the relevent metadata for the Detection job. As part of the
	 * metadata contained in this Text Data, will be the Identifier to the Piazza Data Item that will contain the
	 * GeoJSON detection. This function will parse out that Data ID and fetch the detection GeoJSON from that Data ID.
	 * 
	 * @param dataId
	 *            The Data ID of the Service Execution Job Metadata
	 * @param job
	 *            The Job object. Used mostly for just reporting accurate logging upon failures.
	 * @return The raw GeoJSON bytes of the shoreline detection.
	 */
	public byte[] getBytesFromSuccessfulServiceJobData(String dataId, Job job) throws UserException {
		piazzaLogger.log(
				String.format("Attempting to download GeoJSON data from Successful Job %s with Data Id %s.", job.getJobId(), dataId),
				Severity.INFORMATIONAL);
		byte[] metadata = downloadData(dataId);
		String geoJsonDataId = null;
		// Parse the real GeoJSON Data ID from the Metadata block
		try {
			JsonNode metadataJson = objectMapper.readTree(metadata);
			geoJsonDataId = metadataJson.get("OutFiles").get("shoreline.geojson").asText();
		} catch (IOException exception) {
			String error = String.format(
					"There was an error parsing the Detection Metadata for Job %s Metadata Data Id %s. The raw content was: %s",
					job.getJobId(), dataId, new String(metadata));
			piazzaLogger.log(error, Severity.ERROR);
			throw new UserException(error, exception, HttpStatus.INTERNAL_SERVER_ERROR);
		}
		// Use the GeoJSON Data ID to fetch the raw GeoJSON Bytes from Piazza
		piazzaLogger.log(String.format("Fetching GeoJSON for Job %s with Data %s from Piazza.", job.getJobId(), geoJsonDataId),
				Severity.INFORMATIONAL);
		return downloadData(geoJsonDataId);
	}

	/**
	 * Returns all of the Statistics for the Beachfront Algorithm as reported by the Piazza Task-Managed service.
	 * 
	 * @return JSON block containing statistics. This contains, at least, the number of jobs in that algorithms queue.
	 */
	public JsonNode getAlgorithmStatistics(String algorithmId) throws UserException {
		String piazzaTaskUrl = String.format("%s/service/%s/task/metadata", PIAZZA_URL, algorithmId);
		piazzaLogger.log(String.format("Fetching Algorithm Tasks Metadata for %s at URL %s", algorithmId, piazzaTaskUrl),
				Severity.INFORMATIONAL);
		HttpHeaders headers = createPiazzaHeaders(PIAZZA_API_KEY);
		HttpEntity<String> request = new HttpEntity<>(headers);

		// Execute the Request
		ResponseEntity<String> response = null;
		try {
			response = restTemplate.exchange(URI.create(piazzaTaskUrl), HttpMethod.GET, request, String.class);
		} catch (HttpClientErrorException | HttpServerErrorException exception) {
			String error = String.format("There was an error fetching Service %s Metadata from Piazza.", algorithmId);
			piazzaLogger.log(error, Severity.ERROR);
			throw new UserException(error, exception.getMessage(), exception.getStatusCode());
		}

		try {
			JsonNode jsonNode = objectMapper.readTree(response.getBody());
			return jsonNode;
		} catch (IOException exception) {
			String error = String.format("There was an error parsing the Service Metadata for service %s.", algorithmId);
			piazzaLogger.log(error, Severity.ERROR);
			throw new UserException(error, exception, HttpStatus.INTERNAL_SERVER_ERROR);
		}
	}

	/**
	 * Wraps up a Piazza Service JSON Node (from a /service response) in an Algorithm Object
	 * 
	 * @param serviceNode
	 *            The Service Data Node
	 * @return The Algorithm
	 */
	private Algorithm getAlgorithmFromServiceNode(JsonNode algorithmJson) {
		JsonNode metadata = algorithmJson.get("resourceMetadata");
		JsonNode addedMetadata = metadata.get("metadata");
		Algorithm algorithm = new Algorithm(metadata.get("description").asText(), addedMetadata.get("Interface").asText(),
				addedMetadata.get("ImgReq - cloudCover").asInt(), metadata.get("name").asText(), algorithmJson.get("serviceId").asText(),
				metadata.get("version").asText());
		return algorithm;
	}

	/**
	 * Creates Basic Auth headers with the Piazza API Key
	 * 
	 * @param piazzaApiKey
	 *            The Piazza API Key
	 * @return Basic Auth Headers for Piazza
	 */
	private HttpHeaders createPiazzaHeaders(String piazzaApiKey) {
		String plainCreds = piazzaApiKey + ":";
		byte[] plainCredsBytes = plainCreds.getBytes();
		byte[] base64CredsBytes = Base64.encodeBase64(plainCredsBytes);
		String base64Creds = new String(base64CredsBytes);
		HttpHeaders headers = new HttpHeaders();
		headers.add("Authorization", "Basic " + base64Creds);
		headers.setContentType(MediaType.APPLICATION_JSON);
		return headers;
	}

	/**
	 * Gets the JSON for a Piazza job request, with string format parameters that must be filled in
	 * 
	 * @return JSON job request template
	 */
	private String loadJobRequestJson() throws Exception {
		// Create the JSON Payload for the Layer request to GeoServer
		ClassLoader classLoader = getClass().getClassLoader();
		InputStream jsonStream = null;
		String jsonString = null;
		try {
			jsonStream = classLoader.getResourceAsStream(String.format("%s%s%s", "piazza", File.separator, "execute.json"));
			jsonString = IOUtils.toString(jsonStream, "UTF-8");
		} finally {
			try {
				if (jsonStream != null) {
					jsonStream.close();
				}
			} catch (Exception exception) {
				exception.printStackTrace();
			}
		}
		return jsonString;
	}
}
