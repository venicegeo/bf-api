package org.venice.beachfront.bfapi;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.http.HeaderElement;
import org.apache.http.HeaderElementIterator;
import org.apache.http.HttpResponse;
import org.apache.http.client.HttpClient;
import org.apache.http.conn.ConnectionKeepAliveStrategy;
import org.apache.http.conn.ssl.NoopHostnameVerifier;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.message.BasicHeaderElementIterator;
import org.apache.http.protocol.HTTP;
import org.apache.http.protocol.HttpContext;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
import org.springframework.web.servlet.handler.HandlerInterceptorAdapter;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.joda.JodaModule;

@Configuration
public class BfApiConfig {
	@Value("${http.max.total}")
	private int httpMaxTotal;
	@Value("${http.max.route}")
	private int httpMaxRoute;

	@Bean
	public ObjectMapper getJacksonObjectMapper() {
		ObjectMapper mapper = new ObjectMapper();
		mapper.registerModule(new JodaModule());
		return mapper;
	}

	@SuppressWarnings("resource") // httpClient should stay open and that's OK
	@Bean
	public RestTemplate restTemplate() {
		RestTemplate restTemplate = new RestTemplate();
		HttpClient httpClient = HttpClients.custom().setMaxConnTotal(httpMaxTotal).setMaxConnPerRoute(httpMaxRoute)
				.setKeepAliveStrategy(new ConnectionKeepAliveStrategy() {
					@Override
					public long getKeepAliveDuration(HttpResponse response, HttpContext context) {
						HeaderElementIterator it = new BasicHeaderElementIterator(response.headerIterator(HTTP.CONN_KEEP_ALIVE));
						while (it.hasNext()) {
							HeaderElement headerElement = it.nextElement();
							String param = headerElement.getName();
							String value = headerElement.getValue();
							if (value != null && param.equalsIgnoreCase("timeout")) {
								return Long.parseLong(value) * 1000;
							}
						}
						return 5 * 1000; // TODO: Probably want this configurable
					}
				}).setSSLHostnameVerifier(new NoopHostnameVerifier()).build();
		restTemplate.setRequestFactory(new HttpComponentsClientHttpRequestFactory(httpClient));
		return restTemplate;
	}

	@Bean
	public ObjectMapper objectMapper() {
		return new ObjectMapper();
	}

	@Bean
	public ExecutorService getExecutor(@Value("${concurrent.threads}") int threads) {
		return Executors.newFixedThreadPool(threads);
	}

	@Configuration
	protected static class AddCorsHeaders extends WebMvcConfigurerAdapter {
		@Override
		public void addInterceptors(InterceptorRegistry registry) {
			registry.addInterceptor(new HandlerInterceptorAdapter() {
				@Override
				public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
					response.setHeader("Access-Control-Allow-Headers", "authorization, content-type");
					response.setHeader("Access-Control-Allow-Origin", "*");
					response.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
					response.setHeader("Access-Control-Max-Age", "36000");
					return true;
				}
			});
		}
	}
}
