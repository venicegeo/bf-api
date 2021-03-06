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
package org.venice.beachfront.bfapi.auth.jwt;

import java.io.IOException;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.jwt.Jwt;
import org.springframework.stereotype.Component;
import org.venice.beachfront.bfapi.auth.BfAuthenticationToken;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.UserProfileService;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import model.logger.Severity;
import util.GeoAxisJWTUtility;
import util.PiazzaLogger;

/**
 * Handles the authentication and authorization for all REST Requests that define Bearer Authentication, in the form of
 * JWTs. This will validate and verify the JWT Tokens and associate the JWT request with the User Profile that contains
 * the Distinguished Name as stated in the JWT token.
 * <p>
 * In present form, JWT tokens will only be valid for users who have already authenticated via OAuth, and as such
 * already have a UserProfile in the Beachfront system.
 */
@Component
public class JWTAuthProvider implements AuthenticationProvider {
	@Autowired
	private UserProfileService userProfileService;
	@Autowired
	private PiazzaLogger piazzaLogger;
	@Autowired
	private GeoAxisJWTUtility jwtUtility;
	@Autowired
	private ObjectMapper objectMapper;

	@Value("${jwt.enabled}")
	private Boolean jwtEnabled;

	@Override
	public Authentication authenticate(final Authentication authentication) throws AuthenticationException {
		// Ensure JWT is Enabled
		if (!jwtEnabled.booleanValue()) {
			throw new JWTAuthenticationException("JWT authentication is not enabled.");
		}

		// Check for the validity of the JWT
		final String encodedJwt = authentication.getPrincipal().toString();
		final Jwt jwt = jwtUtility.decodeAndVerify(encodedJwt);
		if (jwt == null) {
			final String error = "JWT received from the client that could not be verified.";
			piazzaLogger.log(error, Severity.INFORMATIONAL);
			throw new JWTAuthenticationException(error);
		}

		// Get the DN from the JWT Payload and retrieve the User Profile
		String dn = null;
		JsonNode payloadJson = null;
		try {
			final String jwtPayload = jwt.getClaims();
			payloadJson = objectMapper.readTree(jwtPayload);
			final JsonNode dnNode = payloadJson.get("dn");
			if (dnNode == null) {
				throw new IOException("Distinguished Name from JWT Payload is not provided.");
			}
			dn = payloadJson.get("dn").asText();
			if ((dn == null) || (dn == "")) {
				throw new IOException("Distinguished Name from JWT Payload is empty or blank.");
			}
		} catch (IOException exception) {
			final String error = String.format("Valid JWT received from the client, but could not read DN from Payload with error: %s.",
					exception.getMessage());
			piazzaLogger.log(error, Severity.ERROR);
			throw new JWTAuthenticationException(error);
		}

		// Check the expiration
		long expirationEpochSeconds = payloadJson.get("exp").asLong();
		// Convert Java epoch of milliseconds to match the JWT epoch of seconds
		if ((DateTime.now().getMillis() / 1000) > expirationEpochSeconds) {
			final String error = String.format("Received an expired JWT token from Client DN %s. Will not process request.", dn);
			piazzaLogger.log(error, Severity.INFORMATIONAL);
			throw new JWTAuthenticationException(error);
		}

		// Get the User Profile for the DN
		final UserProfile userProfile = userProfileService.getUserProfileById(dn);
		if (userProfile == null) {
			final String error = String.format(
					"Attempted to retrieve User Profile by DN %s from JWT token, but the User Profile could not be found. The request cannot be authenticated.",
					dn);
			piazzaLogger.log(error, Severity.INFORMATIONAL);
			throw new JWTAuthenticationException(error);
		}

		// Update the last access date for this User Profile
		userProfileService.updateLastAccessed(userProfile);
		return new BfAuthenticationToken(userProfile, null);
	}

	@Override
	public boolean supports(Class<?> authentication) {
		return authentication.equals(JWTToken.class);
	}

}
