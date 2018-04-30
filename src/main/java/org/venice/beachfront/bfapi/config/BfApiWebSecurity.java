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
		web.ignoring().antMatchers("/").antMatchers("/index").antMatchers("/login").antMatchers("/oauth/start").antMatchers(HttpMethod.OPTIONS);
	}

	@Override
	protected void configure(HttpSecurity http) throws Exception {
		// @formatter:off
		http
			.httpBasic()
			.authenticationEntryPoint(failureEntryPoint)
			.authenticationDetailsSource(authenticationDetailsSource())
		.and()
			.authorizeRequests()
			.anyRequest()
			.authenticated()
		.and()
			.sessionManagement()
			.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
		.and()
			.csrf()
			.disable();
		// @formatter:on
	}

	private AuthenticationDetailsSource<HttpServletRequest, ExtendedRequestDetails> authenticationDetailsSource() {
		return (request) -> {return new ExtendedRequestDetails(request); };
	}
}