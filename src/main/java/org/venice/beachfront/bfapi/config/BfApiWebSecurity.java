package org.venice.beachfront.bfapi.config;

import javax.servlet.http.HttpServletRequest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationDetailsSource;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.builders.WebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.venice.beachfront.bfapi.auth.ApiKeyAuthProvider;
import org.venice.beachfront.bfapi.auth.ExtendedRequestDetails;
import org.venice.beachfront.bfapi.auth.FailedAuthEntryPoint;

/**
 * Initializes the security providers for validating API Keys on all requests that require API Key validation.
 */
@Configuration
public class BfApiWebSecurity extends WebSecurityConfigurerAdapter {

	@Autowired
	private ApiKeyAuthProvider apiKeyAuthProvider;

	@Autowired
	private FailedAuthEntryPoint failureEntryPoint;

	@Override
	protected void configure(AuthenticationManagerBuilder auth) throws Exception {
		auth.authenticationProvider(apiKeyAuthProvider);
	}

	@Override
	public void configure(WebSecurity web) throws Exception {
		// @formatter:off

		web.ignoring()

			// Allow unauthenticated queries to root (health check) path
			.antMatchers("/") 

			// Allow unauthenticated queries to login callback path
			.antMatchers("/oauth/callback")

			// Allow unauthenticated queries to OAuth login start path
			.antMatchers("/oauth/start") 

			// Allow unauthenticated queries for Swagger documentation
			.antMatchers("/v2/api-docs")

			// Allow any OPTIONS for REST best practices
			.antMatchers(HttpMethod.OPTIONS); 

		// @formatter:on
	}

	@Override
	protected void configure(HttpSecurity http) throws Exception {
		// @formatter:off
		http
			// Use HTTP Basic authentication
			.httpBasic()

			// Entry point for starting a Basic auth exchange (i.e. "failed authentication" handling)
			.authenticationEntryPoint(failureEntryPoint)

			// Feed more request details into any providers
			.authenticationDetailsSource(authenticationDetailsSource()) 
		.and()
			.authorizeRequests()
			.anyRequest()
			.authenticated()
		.and()
			// Do not create or manage sessions for security
			.sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
		.and()
			// Disable auto-magical Spring Security logout behavior
			.logout().disable()

			// Use this custom authentication provider to authenticate requests
			.authenticationProvider(apiKeyAuthProvider)

			// Disable advanced CSRF protections for better statelessness
			.csrf().disable();

		// @formatter:on
	}

	private AuthenticationDetailsSource<HttpServletRequest, ExtendedRequestDetails> authenticationDetailsSource() {
		return (request) -> {return new ExtendedRequestDetails(request); };
	}
}