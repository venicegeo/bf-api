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
	private String COOKIE_NAME;

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
			if (cookies != null) {
				for (Cookie cookie : Arrays.asList(cookies)) {
					if (COOKIE_NAME.equals(cookie.getName())) {
						apiKey = cookie.getValue();
					}
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
		piazzaLogger.log("Invalid or Expired Authentication API Key received from the client. Discarding request. key=" + apiKey, Severity.ERROR);
		return null;
	}

	@Override
	public boolean supports(Class<?> authentication) {
		return authentication.equals(UsernamePasswordAuthenticationToken.class);
	}

}
