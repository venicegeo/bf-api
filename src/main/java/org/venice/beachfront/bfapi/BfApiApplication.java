package org.venice.beachfront.bfapi;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Main application class.
 * 
 * Sets up the Spring Boot environment to launch BF API.
 * 
 * @version 2.0
 */
@SpringBootApplication
public class BfApiApplication {

	public static void main(String[] args) {
		SpringApplication.run(BfApiApplication.class, args);
	}
}
