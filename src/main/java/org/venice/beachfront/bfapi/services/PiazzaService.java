package org.venice.beachfront.bfapi.services;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.util.List;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.io.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import org.venice.beachfront.bfapi.model.exception.UserException;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class PiazzaService {
	@Value("${piazza.server}")
	private String PIAZZA_URL;
	@Value("${PIAZZA_API_KEY}")
	private String PIAZZA_API_KEY;

	@Autowired
	private RestTemplate restTemplate;

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
		HttpHeaders headers = createPiazzaHeaders(PIAZZA_API_KEY);
		// Structure the Job Request
		String requestJson = null;
		try {
			requestJson = String.format(loadJobRequestJson(), serviceId, cliCommand, String.join(", ", fileNames),
					String.join(", ", fileUrls), userId);
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
		ObjectMapper objectMapper = new ObjectMapper();
		String jobId = null;
		try {
			JsonNode responseJson = objectMapper.readTree(response.getBody());
			jobId = responseJson.get("data").get("jobId").asText();
		} catch (IOException exception) {
			throw new UserException("There was an error parsing the Piazza response when submitting the Job.", exception.getMessage(),
					HttpStatus.INTERNAL_SERVER_ERROR);
		}
		return jobId;
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
			jsonStream = classLoader.getResourceAsStream(String.format("%s/%s", "piazza", File.separator, "execute.json"));
			jsonString = IOUtils.toString(jsonStream);
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
