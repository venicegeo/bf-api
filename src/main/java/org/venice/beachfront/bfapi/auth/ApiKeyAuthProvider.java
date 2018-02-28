package org.venice.beachfront.bfapi.auth;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.stereotype.Component;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.UserProfileService;

import model.logger.Severity;
import util.PiazzaLogger;

/**
 * Handles the authentication and authorization for all REST Controller methods to the API that require API Key
 * authentication.
 * <p>
 * This is utilized once the user has received their API Key through OAuth controllers.
 */
@Component
public class ApiKeyAuthProvider implements AuthenticationProvider {
	@Autowired
	private UserProfileService userProfileService;
	@Autowired
	private PiazzaLogger piazzaLogger;

	@Override
	public Authentication authenticate(Authentication authentication) throws AuthenticationException {
		String apiKey = authentication.getName();
		UserProfile userProfile = userProfileService.getUserProfileByApiKey(apiKey);
		if (userProfile != null) {
			// Valid API Key. Update the last time of access to now.
			userProfileService.updateLastAccessed(userProfile);
			// Return the Token
			return new UsernamePasswordAuthenticationToken(userProfile, apiKey);
		}
		// Invalid Key
		piazzaLogger.log("Invalid Authentication API Key received from the client. Discarding request.", Severity.ERROR);
		return null;
	}

	@Override
	public boolean supports(Class<?> authentication) {
		return authentication.equals(UsernamePasswordAuthenticationToken.class);
	}

}
