package org.venice.beachfront.bfapi;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.sql.DataSource;

import java.net.MalformedURLException;
import java.net.URL;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.jdbc.DataSourceBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurerAdapter;
import org.springframework.web.servlet.handler.HandlerInterceptorAdapter;
import org.venice.beachfront.bfapi.model.Environment;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.joda.JodaModule;

@Configuration
@PropertySource("classpath:application.properties")
public class BfApiConfig {
	@Bean
	public ObjectMapper getJacksonObjectMapper() {
		ObjectMapper mapper = new ObjectMapper();
		mapper.registerModule(new JodaModule());
		return mapper;
	}
	
	@Bean
	public Environment getEnvironmentConfiguration(@Value("${IA_BROKER}") String iaBroker) throws MalformedURLException  {
		URL iaBrokerBaseUrl = new URL(iaBroker);
		
		return new Environment() {
			public URL getIABrokerBaseUrl() {
				return iaBrokerBaseUrl;
			}
		};
	}
	
	@Bean 
	public ExecutorService getExecutor(@Value("${concurrent.threads}") int threads) {
		return Executors.newFixedThreadPool(threads);
	}

	@Bean
	public DataSource getDataSource(
			@Value("${DATABASE_URL:#{null}}") String environmentDbUrl,
			@Value("${vcap.services.pz-postgres.credentials.hostname:#{null}}") String vcapHostname,
			@Value("${vcap.services.pz-postgres.credentials.port:#{null}}") String vcapPort,
			@Value("${vcap.services.pz-postgres.credentials.database:#{null}}") String vcapDatabase,
			@Value("${vcap.services.pz-postgres.credentials.username:#{null}}") String vcapUsername,
			@Value("${vcap.services.pz-postgres.credentials.password:#{null}}") String vcapPassword
			) {
		if (environmentDbUrl != null && environmentDbUrl.length() > 0) {
			return DataSourceBuilder
					.create()
					.driverClassName("org.postgresql.Driver")
					.url(environmentDbUrl)
					.build();
		}
		
		
		if (vcapHostname == null || vcapPort == null || vcapDatabase == null || vcapUsername == null || vcapPassword == null) {
			throw new RuntimeException("Could not initialize database from env DATABASE_URL or vcap");
		}
		
		return DataSourceBuilder
				.create()
				.driverClassName("org.postgresql.Driver")
				.url(String.format("jdbc:postgresql://%s:%s/%s", vcapHostname, vcapPort, vcapDatabase))
				.username(vcapUsername)
				.password(vcapPassword)
				.build();
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
