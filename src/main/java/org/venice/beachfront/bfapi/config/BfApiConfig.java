package org.venice.beachfront.bfapi.config;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.joda.JodaModule;

@Configuration
public class BfApiConfig {

	@Bean
	public ObjectMapper getJacksonObjectMapper() {
		ObjectMapper mapper = new ObjectMapper();
		mapper.registerModule(new JodaModule());
		return mapper;
	}

	@Bean
	public ExecutorService getExecutor(@Value("${concurrent.threads}") int threads) {
		return Executors.newFixedThreadPool(threads);
	}
}