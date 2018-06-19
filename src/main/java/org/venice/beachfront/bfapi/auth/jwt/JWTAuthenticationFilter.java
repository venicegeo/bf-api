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

import java.io.IOException;

import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Filter for JWT Bearer tokens. This filter will parse requests that contain Bearer token authentication, and if
 * detected, will read that value and attempt to convert it into a proper JWT token that can be evaluated by the
 * downstream JWT Authentication Provider.
 * 
 * @author Patrick.Doody
 *
 */
public class JWTAuthenticationFilter extends OncePerRequestFilter {
	private AuthenticationManager authenticationManager;

	public JWTAuthenticationFilter(AuthenticationManager authenticationManager) {
		this.authenticationManager = authenticationManager;
	}

	@Override
	protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
			throws ServletException, IOException {
		// Do nothing if the header does not contain the Bearer prefix
		String header = request.getHeader("Authorization");
		if (header == null || !header.startsWith("Bearer ")) {
			chain.doFilter(request, response);
			return;
		}

		// Create JWT Token wrapping from the Bearer value, and pass to the authentication manager to verify
		String encodedJwt = header.split(" ")[1];
		JWTToken token = new JWTToken(encodedJwt);
		Authentication authResult = this.authenticationManager.authenticate(token);
		SecurityContextHolder.getContext().setAuthentication(authResult);

		// Continue filtering
		chain.doFilter(request, response);
	}

}