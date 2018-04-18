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

import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.authentication.www.BasicAuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import model.logger.Severity;
import util.PiazzaLogger;

/**
 * Handles failed authentication provider responses back to the user for when the user has submitted an invalid API Key.
 */
@Component
public class FailedAuthEntryPoint extends BasicAuthenticationEntryPoint {
	@Autowired
	private PiazzaLogger piazzaLogger;
	
	@Override
	public void commence(HttpServletRequest request, HttpServletResponse response, AuthenticationException authEx)
			throws IOException, ServletException {
		response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
		response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Authentication Failed");
		PrintWriter writer = response.getWriter();
		writer.println("Invalid API Key specified.");

		String message = String.format("Authentication Failed; Authorization header=`%s`; AuthenticationException=`%s`",
				request.getHeader("Authorization"),
				(authEx != null) ? authEx.toString() : "null");
		this.piazzaLogger.log(message, Severity.WARNING);
	}

	@Override
	public void afterPropertiesSet() throws Exception {
		setRealmName("Beachfront");
		super.afterPropertiesSet();
	}
}
