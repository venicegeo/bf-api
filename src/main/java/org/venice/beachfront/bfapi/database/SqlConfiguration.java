package org.venice.beachfront.bfapi.database;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;

import java.io.IOException;
import java.nio.charset.Charset;

import org.apache.commons.io.IOUtils;

@Configuration
public class SqlConfiguration {
	@Bean(name="jobExists.sql")
	public String getJobExistsSql(@Value("classpath:sql/application/jobExists.sql") Resource resource) throws IOException {
		return IOUtils.toString(resource.getInputStream(), Charset.defaultCharset());
	}
	
	@Bean(name="insertJob.sql")
	public String insertJobSql(@Value("classpath:sql/application/insertJob.sql") Resource resource) throws IOException {
		return IOUtils.toString(resource.getInputStream(), Charset.defaultCharset());
	}
	
	
	@Bean(name="selectJob.sql")
	public String getSelectJobSql(@Value("classpath:sql/application/selectJob.sql") Resource resource) throws IOException {
		return IOUtils.toString(resource.getInputStream(), Charset.defaultCharset());
	}

	@Bean(name="selectAllJobs.sql")
	public String getSelectAllJobsSql(@Value("classpath:sql/application/selectAllJobs.sql") Resource resource) throws IOException {
		return IOUtils.toString(resource.getInputStream(), Charset.defaultCharset());
	}

	@Bean(name="selectJobByInputs.sql")
	public String getSelectJobByInputsSql(@Value("classpath:sql/application/selectJobByInputs.sql") Resource resource) throws IOException {
		return IOUtils.toString(resource.getInputStream(), Charset.defaultCharset());
	}	
}
