/**
 * Copyright 2018, Radiant Solutions, Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
package org.venice.beachfront.bfapi;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.ComponentScan.Filter;
import org.springframework.context.annotation.FilterType;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * Main application class.
 * 
 * Sets up the Spring Boot environment to launch BF API.
 * 
 * @version 2.0
 */
@SpringBootApplication
@EnableSwagger2
@EnableTransactionManagement
@EnableJpaRepositories(excludeFilters = { @Filter(type = FilterType.REGEX, pattern = "model.*.*"),
		@Filter(type = FilterType.REGEX, pattern = "org.venice.piazza.common.hibernate.*.*") })
@ComponentScan(basePackages = { "org.venice.beachfront", "util" })
public class BfApiApplication {

	public static void main(String[] args) {
		SpringApplication.run(BfApiApplication.class, args);
	}
}
