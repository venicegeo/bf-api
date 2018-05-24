package org.venice.beachfront.bfapi.config;

import org.apache.http.client.HttpClient;
import org.apache.http.conn.ssl.NoopHostnameVerifier;
import org.apache.http.impl.client.HttpClientBuilder;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.http.converter.FormHttpMessageConverter;
import org.springframework.web.client.RestTemplate;
import org.venice.beachfront.bfapi.geoserver.AuthHeaders;
import org.venice.beachfront.bfapi.geoserver.BasicAuthHeaders;

/**
 * Configures the API to use basic HTTP authentication when communicating with GeoServer
 */
@Configuration
@Profile({ "basic-geoserver-auth" })
public class GeoServerBasicAuthenticationConfig extends GeoServerBaseAuthenticationConfig {

	@Value("${http.max.total}")
	private int httpMaxTotal;

	@Value("${http.max.route}")
	private int httpMaxRoute;

	@Bean
	public HttpClient httpClient() {
		// @formatter:off
		return HttpClientBuilder.create()
					.setMaxConnTotal(httpMaxTotal)
					.setMaxConnPerRoute(httpMaxRoute)
					.setSSLHostnameVerifier(new NoopHostnameVerifier())
					.setKeepAliveStrategy(getKeepAliveStrategy())
					.build();
		// @formatter:on
	}

	@Bean
	public RestTemplate restTemplate(@Autowired HttpClient httpClient) {
		final RestTemplate restTemplate = new RestTemplate();
		restTemplate.setRequestFactory(new HttpComponentsClientHttpRequestFactory(httpClient));
		restTemplate.getMessageConverters().add(new FormHttpMessageConverter());
		return restTemplate;
	}

	@Bean
	public AuthHeaders authHeaders() {
		return new BasicAuthHeaders();
	}
}