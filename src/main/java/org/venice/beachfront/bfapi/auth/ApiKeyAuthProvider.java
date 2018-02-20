package org.venice.beachfront.bfapi.auth;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.UserProfileService;

/**
 * Handles the authentication and authorization for all REST Controller methods to the API that require API Key
 * authentication.
 * <p>
 * This is utilized once the user has received their API Key through OAuth controllers.
 */
public class ApiKeyAuthProvider implements AuthenticationProvider {
	@Autowired
	private UserProfileService userProfileService;

	@Override
	public Authentication authenticate(Authentication authentication) throws AuthenticationException {
		String apiKey = authentication.getName();
		UserProfile userProfile = userProfileService.getUserProfileByApiKey(apiKey);
		if (userProfile != null) {
			// Valid API Key
			return new UsernamePasswordAuthenticationToken(userProfile.getUserId(), null);
		}
		// Invalid Key
		return null;
	}

	@Override
	public boolean supports(Class<?> authentication) {
		return authentication.equals(UsernamePasswordAuthenticationToken.class);
	}

}
