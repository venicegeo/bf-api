/**
 * Copyright 2018, Radiant Solutions, Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
// * you may not use this file except in compliance with the License.
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

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.authentication.AbstractAuthenticationProcessingFilter;
import org.springframework.security.web.util.matcher.RequestMatcher;

/**
 * Filter for JWT Bearer tokens
 * 
 * @author Patrick.Doody
 *
 */
public class JWTAuthenticationFilter extends AbstractAuthenticationProcessingFilter {

	public JWTAuthenticationFilter() {
		super(new RequestMatcher() {

			@Override
			public boolean matches(HttpServletRequest request) {
				boolean isBearer = request.getHeader("Authorization").startsWith("Bearer");
				return isBearer;
			}
		});
	}

	@Override
	public Authentication attemptAuthentication(HttpServletRequest req, HttpServletResponse res) throws AuthenticationException {
		String authHeader = req.getHeader("Authorization");
		if (authHeader.startsWith("Bearer")) {
			JWTToken token = new JWTToken("Test", "Test");
			//token.setAuthenticated(false);
			return this.getAuthenticationManager().authenticate(token);
		} else {
			return null;
		}
	}

}