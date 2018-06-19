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

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.stereotype.Component;
import org.venice.beachfront.bfapi.auth.BfAuthenticationToken;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.UserProfileService;

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

	@Override
	public Authentication authenticate(Authentication authentication) throws AuthenticationException {
		return new BfAuthenticationToken(new UserProfile(), "Testing");
	}

	@Override
	public boolean supports(Class<?> authentication) {
		return authentication.equals(JWTToken.class);
	}

}
