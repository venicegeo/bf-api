package org.venice.beachfront.bfapi.services;

import static org.junit.Assert.assertEquals;

import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;

import org.apache.commons.io.IOUtils;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.mockito.Spy;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.piazza.StatusMetadata;

import com.fasterxml.jackson.databind.ObjectMapper;

import util.PiazzaLogger;

public class PiazzaServiceTests {
	@Mock
	private RestTemplate restTemplate;
	@Spy
	private ObjectMapper objectMapper;
	@Mock
	private PiazzaLogger piazzaLogger;
	@InjectMocks
	private PiazzaService piazzaService;

	@Before
	public void setup() {
		MockitoAnnotations.initMocks(this);

		ReflectionTestUtils.setField(piazzaService, "PIAZZA_URL", "https://piazza.com");
		ReflectionTestUtils.setField(piazzaService, "PIAZZA_API_KEY", "piazzaKey");
	}

	@Test
	public void testNominalExecution() throws UserException, IOException {
		// Mock
		String responseJson = IOUtils.toString(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "piazza", File.separator, "postJob.json")),
				"UTF-8");
		Mockito.when(restTemplate.exchange(Mockito.<URI>any(), Mockito.eq(HttpMethod.POST), Mockito.<HttpEntity<String>>any(),
				Mockito.<Class<String>>any())).thenReturn(new ResponseEntity<String>(responseJson, HttpStatus.OK));
		// Test
		String jobId = piazzaService.execute("serviceId", "--test 1", new ArrayList<String>(), new ArrayList<String>(), "tester");
		// Assert
		assertEquals(jobId, "job123");
	}

	@Test(expected = UserException.class)
	public void testPiazzaErrorResponse() throws UserException {
		// Mock
		Mockito.when(restTemplate.exchange(Mockito.<URI>any(), Mockito.eq(HttpMethod.POST), Mockito.<HttpEntity<String>>any(),
				Mockito.<Class<String>>any())).thenThrow(new HttpServerErrorException(HttpStatus.INTERNAL_SERVER_ERROR));
		// Test
		piazzaService.execute("serviceId", "--test 1", new ArrayList<String>(), new ArrayList<String>(), "tester");
	}

	@Test(expected = UserException.class)
	public void testJsonParseError() throws UserException {
		// Mock
		String responseJson = "{\"data\": { jobId\": \"job123\"}}";
		Mockito.when(restTemplate.exchange(Mockito.<URI>any(), Mockito.eq(HttpMethod.POST), Mockito.<HttpEntity<String>>any(),
				Mockito.<Class<String>>any())).thenReturn(new ResponseEntity<String>(responseJson, HttpStatus.OK));
		// Test
		piazzaService.execute("serviceId", "--test 1", new ArrayList<String>(), new ArrayList<String>(), "tester");
	}

	@Test
	public void testJobStatus() throws UserException, IOException {
		// Mock
		String responseJson = IOUtils.toString(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "piazza", File.separator, "runningJob.json")),
				"UTF-8");
		Mockito.when(restTemplate.exchange(Mockito.<URI>any(), Mockito.eq(HttpMethod.GET), Mockito.<HttpEntity<String>>any(),
				Mockito.<Class<String>>any())).thenReturn(new ResponseEntity<String>(responseJson, HttpStatus.OK));
		// Test
		StatusMetadata status = piazzaService.getJobStatus("job123");
		// Assert
		assertEquals(status.getStatus(), Job.STATUS_RUNNING);
	}

	@Test
	public void testJobStatusSuccess() throws UserException, IOException {
		// Mock
		String responseJson = IOUtils.toString(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "piazza", File.separator, "successJob.json")),
				"UTF-8");
		Mockito.when(restTemplate.exchange(Mockito.<URI>any(), Mockito.eq(HttpMethod.GET), Mockito.<HttpEntity<String>>any(),
				Mockito.<Class<String>>any())).thenReturn(new ResponseEntity<String>(responseJson, HttpStatus.OK));
		// Test
		StatusMetadata status = piazzaService.getJobStatus("job123");
		// Assert
		assertEquals(status.getStatus(), Job.STATUS_SUCCESS);
		assertEquals(status.getDataId(), "TestData123");
	}

	@Test
	public void testJobStatusFailure() throws UserException, IOException {
		// Mock
		String responseJson = IOUtils.toString(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "piazza", File.separator, "errorJob.json")),
				"UTF-8");
		Mockito.when(restTemplate.exchange(Mockito.<URI>any(), Mockito.eq(HttpMethod.GET), Mockito.<HttpEntity<String>>any(),
				Mockito.<Class<String>>any())).thenReturn(new ResponseEntity<String>(responseJson, HttpStatus.OK));
		// Test
		StatusMetadata status = piazzaService.getJobStatus("job123");
		// Assert
		assertEquals(status.getStatus(), Job.STATUS_ERROR);
		assertEquals(status.getErrorMessage(), "Test Error");
	}

	@Test
	public void testAlgorithmList() throws UserException, IOException {
		// Mock
		String responseJson = IOUtils.toString(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "piazza", File.separator, "serviceList.json")),
				"UTF-8");
		Mockito.when(restTemplate.exchange(Mockito.<URI>any(), Mockito.eq(HttpMethod.GET), Mockito.<HttpEntity<String>>any(),
				Mockito.<Class<String>>any())).thenReturn(new ResponseEntity<String>(responseJson, HttpStatus.OK));
		// Test
		List<Algorithm> algorithms = piazzaService.getRegisteredAlgorithms();
		// Assert
		assertEquals(algorithms.size(), 1);
		assertEquals(algorithms.get(0).getName(), "Test Algorithm");
		assertEquals(algorithms.get(0).getDescription(), "Test Description");
		assertEquals(algorithms.get(0).getInterface(), "test-algorithm");
		assertEquals(algorithms.get(0).getMaxCloudCover(), 10);
		assertEquals(algorithms.get(0).getServiceId(), "service123");
		assertEquals(algorithms.get(0).getVersion(), "1.0.0");
	}

	@Test
	public void testAlgorithm() throws UserException, IOException {
		// Mock
		String responseJson = IOUtils.toString(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "piazza", File.separator, "service.json")),
				"UTF-8");
		Mockito.when(restTemplate.exchange(Mockito.<URI>any(), Mockito.eq(HttpMethod.GET), Mockito.<HttpEntity<String>>any(),
				Mockito.<Class<String>>any())).thenReturn(new ResponseEntity<String>(responseJson, HttpStatus.OK));
		// Test
		Algorithm algorithm = piazzaService.getRegisteredAlgorithm("service123");
		// Assert
		assertEquals(algorithm.getName(), "Test Algorithm");
		assertEquals(algorithm.getDescription(), "Test Description");
		assertEquals(algorithm.getInterface(), "test-algorithm");
		assertEquals(algorithm.getMaxCloudCover(), 10);
		assertEquals(algorithm.getServiceId(), "service123");
		assertEquals(algorithm.getVersion(), "1.0.0");
	}

	@Test
	public void testDataDownload() throws UserException {
		// Mock
		String testData = "Test Data";
		Mockito.when(restTemplate.exchange(Mockito.<URI>any(), Mockito.eq(HttpMethod.GET), Mockito.<HttpEntity<String>>any(),
				Mockito.<Class<byte[]>>any())).thenReturn(new ResponseEntity<byte[]>(testData.getBytes(), HttpStatus.OK));
		// Test
		byte[] data = piazzaService.downloadData("data123");
		// Assert
		assertEquals(new String(data), testData);
	}
}
