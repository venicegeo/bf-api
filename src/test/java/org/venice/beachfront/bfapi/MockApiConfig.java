package org.venice.beachfront.bfapi;

import java.net.MalformedURLException;
import java.net.URL;

import javax.sql.DataSource;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.venice.beachfront.bfapi.model.Environment;
import org.venice.beachfront.bfapi.services.JobService;

@Configuration
public class MockApiConfig extends BfApiConfig {
	@Bean
	@Primary
	public Environment getEnvironmentConfiguration() throws MalformedURLException  {
		URL url = new URL("http://localhost:99999");
		return new Environment() {
			public URL getIABrokerBaseUrl() {
				return url;
			}
		};
	}
	
	@Bean
	@Primary
	public DataSource getDataSource() {
		DataSource src = new EmbeddedDatabaseBuilder().build();
		System.err.println("Mock data source: " + src.toString());
		return src;
	}
	
	@Bean
	@Primary
	public JobService getJobService() {
		return null;
	}
}
