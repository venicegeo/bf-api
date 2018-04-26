package org.venice.beachfront.bfapi.controllers;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.Before;
import org.junit.Test;
import org.mockito.*;
import org.venice.beachfront.bfapi.geoserver.GeoserverEnvironment;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.JobService;
import org.venice.beachfront.bfapi.services.PiazzaService;
import org.venice.beachfront.bfapi.services.UptimeService;

import java.util.ArrayList;
import java.util.Map;

public class HealthCheckControllerTest {

    @Mock
    UptimeService uptimeService;
    @Mock
    PiazzaService piazzaService;
    @Mock
    JobService jobService;
    @Mock
    GeoserverEnvironment geoserverEnvironment;

    @InjectMocks
    HealthCheckController healthCheckController;

    @Before
    public void setup() {
        MockitoAnnotations.initMocks(this);
    }

    @Test
    public void healthCheck() throws Exception {
        ArrayList<Algorithm> algorithms = new ArrayList<>();
        algorithms.add(new Algorithm("algo_desc_1", "interface_1", 1, "name_1", "service_id_1", "version_1"));
        algorithms.add(new Algorithm("algo_desc_2", "interface_2", 1, "name_2", "service_id_2", "version_2"));

        ObjectMapper mapper = new ObjectMapper();
        JsonNode stats = mapper.readTree("{\"totalJobCount\": 5}");

        Mockito.when(this.piazzaService.getRegisteredAlgorithms()).thenReturn(algorithms);
        Mockito.when(this.piazzaService.getAlgorithmStatistics(Matchers.anyString()))
                .thenReturn(stats)
                .thenReturn(stats)
                .thenThrow(UserException.class);

        Map<String, String> result = this.healthCheckController.healthCheck();
        Map<String, String> result_ex = this.healthCheckController.healthCheck();
    }
}