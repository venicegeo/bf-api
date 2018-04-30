package org.venice.beachfront.bfapi.config;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.core.Authentication;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.joda.JodaModule;

import io.swagger.annotations.ApiOperation;
import springfox.documentation.builders.ApiInfoBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;

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

	@Bean
	public Docket beachfrontApi() {
		// @formatter:off
		final ApiInfo apiInfo =
				new ApiInfoBuilder()
					.title("Beachfront API")
					.description("Beachfront Web Services")
					.contact(new Contact("The VeniceGeo Project", "http://radiantblue.com", "venice@radiantblue.com"))
					.version("0.1.0")
					.build();

		return new Docket(DocumentationType.SWAGGER_2)
				.useDefaultResponseMessages(false)
				.ignoredParameterTypes(Authentication.class)
				.groupName("Beachfront")
				.apiInfo(apiInfo)
				.select()
				.apis(RequestHandlerSelectors.withMethodAnnotation(ApiOperation.class))
				.paths(PathSelectors.any())
				.build();
		// @formatter:on
	}
}