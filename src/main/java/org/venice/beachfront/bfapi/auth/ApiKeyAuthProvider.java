package org.venice.beachfront.bfapi.auth;

import java.util.Arrays;

import javax.servlet.http.Cookie;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
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
	@Value("${cookie.name}")
	private String COOKIE_NAME; // TODO: This present value is not necessary and should be removed

	@Autowired
	private UserProfileService userProfileService;
	@Autowired
	private PiazzaLogger piazzaLogger;

	@Override
	public Authentication authenticate(Authentication authentication) throws AuthenticationException {
		// First attempt to read the API Key from the auth header
		String apiKey = authentication.getName();
		if (apiKey == null || "".equals(apiKey)) { // TODO: This should not be necessary!
			// No API Key set in auth header. Read the cookie.
			ExtendedRequestDetails details = (ExtendedRequestDetails) authentication.getDetails();
			Cookie[] cookies = details.getRequest().getCookies();
			for (Cookie cookie : Arrays.asList(cookies)) {
				if (COOKIE_NAME.equals(cookie.getName())) {
					apiKey = cookie.getValue();
				}
			}
		}

		UserProfile userProfile = userProfileService.getUserProfileByApiKey(apiKey);
		if (userProfile != null) {
			// Valid API Key. Update the last time of access to now.
			userProfileService.updateLastAccessed(userProfile);
			// Return the Token
			return new BfAuthenticationToken(userProfile, apiKey);
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
