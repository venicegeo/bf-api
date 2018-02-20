package org.venice.beachfront.bfapi.auth;

import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;

/**
 * Handles the authentication and authorization for all REST Controller methods to the API that require API Key
 * authentication.
 * <p>
 * This is utilized once the user has received their API Key through OAuth controllers.
 */
public class ApiKeyAuthProvider implements AuthenticationProvider {

	@Override
	public Authentication authenticate(Authentication authentication) throws AuthenticationException {
		ExtendedRequestDetails details = (ExtendedRequestDetails) authentication.getDetails();
		// TODO: Return a proper auth token if success, return null if no success
		return null;
	}

	@Override
	public boolean supports(Class<?> authentication) {
		return authentication.equals(UsernamePasswordAuthenticationToken.class);
	}

}
