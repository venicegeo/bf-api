package org.venice.beachfront.bfapi.geoserver;

import org.junit.Assert;
import org.junit.Test;
import org.springframework.http.HttpHeaders;

public class BasicAuthHeadersTest {

    @Test
    public void get() {
        BasicAuthHeaders headers = new BasicAuthHeaders();
        Assert.assertNotNull(headers.get());
    }
}