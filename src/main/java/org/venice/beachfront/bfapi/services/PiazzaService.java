package org.venice.beachfront.bfapi.services;

import java.io.File;
import java.io.InputStream;
import java.net.URI;
import java.nio.charset.Charset;
import java.util.List;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.io.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

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
			throws Exception {
		String piazzaJobUrl = String.format("%s/job", PIAZZA_URL);
		HttpHeaders headers = createPiazzaHeaders(PIAZZA_API_KEY);
		// Structure the Job Request
		String requestJson = String.format(loadJobRequestJson(), serviceId, cliCommand, String.join(", ", fileNames),
				String.join(", ", fileUrls), userId);
		HttpEntity<String> request = new HttpEntity<>(requestJson, headers);

		// Execute the Request
		ResponseEntity<String> response = restTemplate.exchange(new URI(piazzaJobUrl), HttpMethod.POST, request, String.class);

		// Parse the Response

		// Return the Job ID

		return null;
	}

	/**
	 * Creates Basic Auth headers with the Piazza API Key
	 * 
	 * @param piazzaApiKey
	 *            The Piazza API Key
	 * @return Basic Auth Headers for Piazza
	 */
	private HttpHeaders createPiazzaHeaders(String piazzaApiKey) {
		return new HttpHeaders() {
			{
				String auth = piazzaApiKey + ":";
				byte[] encodedAuth = Base64.encodeBase64(auth.getBytes(Charset.forName("US-ASCII")));
				String authHeader = "Basic " + new String(encodedAuth);
				set("Authorization", authHeader);
			}
		};
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
