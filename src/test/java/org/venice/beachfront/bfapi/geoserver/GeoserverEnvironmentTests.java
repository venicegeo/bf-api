package org.venice.beachfront.bfapi.geoserver;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.http.client.HttpClient;
import org.junit.Before;
import org.junit.Test;
import org.mockito.*;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import util.PiazzaLogger;

import java.io.IOException;

public class GeoserverEnvironmentTests {

    @Mock
    RestTemplate restTemplate;
    @Mock
    HttpClient httpClient;
    @Mock
    AuthHeaders authHeaders;
    @Mock
    ObjectMapper objectMapper;
    @Mock
    PiazzaLogger piazzaLogger;

    @InjectMocks
    GeoserverEnvironment geoserverEnvironment;


    @Before
    public void setup() {
        MockitoAnnotations.initMocks(this);

        ReflectionTestUtils.setField(this.geoserverEnvironment, "GEOSERVER_HOST", "http://localhost:8080/geoserver");
        ReflectionTestUtils.setField(this.geoserverEnvironment, "LAYER_NAME", "bfdetections");
        ReflectionTestUtils.setField(this.geoserverEnvironment, "LAYER_GROUP_NAME", "bfdetections");
        ReflectionTestUtils.setField(this.geoserverEnvironment, "STYLE_NAME", "bfdetections");
        ReflectionTestUtils.setField(this.geoserverEnvironment, "WORKSPACE_NAME", "piazza");
        ReflectionTestUtils.setField(this.geoserverEnvironment, "DATASTORE_NAME", "piazza");
    }

    @Test
    public void testInitialize_goodResources() {
        ResponseEntity<String> responseEntity = Mockito.mock(ResponseEntity.class);

        Mockito.when(restTemplate.exchange(
                Matchers.anyString(),
                Matchers.eq(HttpMethod.GET),
                Matchers.any(),
                Matchers.eq(String.class)
        )).thenReturn(responseEntity);

        Mockito.when(responseEntity.getStatusCode()).thenReturn(
                HttpStatus.OK
        );

        geoserverEnvironment.initializeEnvironment();
    }

    @Test
    public void testInitialize_missingResources() {
        ResponseEntity<String> responseEntity = Mockito.mock(ResponseEntity.class);

        Mockito.when(restTemplate.exchange(
                Matchers.anyString(),
                Matchers.eq(HttpMethod.GET),
                Matchers.any(),
                Matchers.eq(String.class)
        )).thenReturn(responseEntity);

        HttpClientErrorException ex = new HttpClientErrorException(HttpStatus.NOT_FOUND);
        Mockito.when(responseEntity.getStatusCode())
                .thenThrow(ex);

        geoserverEnvironment.initializeEnvironment();
    }

    @Test
    public void testInitialize_badJson() throws IOException {
        ResponseEntity<String> responseEntity = Mockito.mock(ResponseEntity.class);

        Mockito.when(restTemplate.exchange(
                Matchers.anyString(),
                Matchers.eq(HttpMethod.GET),
                Matchers.any(),
                Matchers.eq(String.class)
        )).thenReturn(responseEntity);

        Mockito.when(this.objectMapper.readTree(Matchers.anyString()))
                .thenThrow(IOException.class);

        geoserverEnvironment.initializeEnvironment();
    }

    @Test
    public void testInitialize_failedPost() {
        ResponseEntity<String> responseEntity = Mockito.mock(ResponseEntity.class);

        HttpClientErrorException ex = new HttpClientErrorException(HttpStatus.NOT_FOUND);
        Mockito.when(responseEntity.getStatusCode())
                .thenThrow(ex);

        Mockito.when(restTemplate.exchange(
                Matchers.anyString(),
                Matchers.eq(HttpMethod.GET),
                Matchers.any(),
                Matchers.eq(String.class)
        )).thenReturn(responseEntity);

        Mockito.when(restTemplate.exchange(
                Matchers.anyString(),
                Matchers.eq(HttpMethod.POST),
                Matchers.any(),
                Matchers.eq(String.class)
        )).thenThrow(ex);

        //Setting this to true causes a System.Exit().
        ReflectionTestUtils.setField(this.geoserverEnvironment, "exitOnGeoServerProvisionFailure", false);

        geoserverEnvironment.initializeEnvironment();
    }

    @Test
    public void testInitialize_restClientException() {
        HttpClientErrorException ex = new HttpClientErrorException(HttpStatus.INTERNAL_SERVER_ERROR);

        Mockito.when(restTemplate.exchange(
                Matchers.anyString(),
                Matchers.eq(HttpMethod.GET),
                Matchers.any(),
                Matchers.eq(String.class)
        ))
                .thenThrow(ex)
                .thenThrow(RestClientException.class);

        geoserverEnvironment.initializeEnvironment();
        geoserverEnvironment.initializeEnvironment();
    }
}
