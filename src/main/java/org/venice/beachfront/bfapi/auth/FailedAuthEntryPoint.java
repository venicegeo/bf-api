package org.venice.beachfront.bfapi.auth;

import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.authentication.www.BasicAuthenticationEntryPoint;

/**
 * Handles failed authentication provider responses back to the user.
 */
public class FailedAuthEntryPoint extends BasicAuthenticationEntryPoint {

	@Override
	public void commence(HttpServletRequest request, HttpServletResponse response, AuthenticationException authEx)
			throws IOException, ServletException {
		PrintWriter writer = response.getWriter();
		writer.println("Auth Failed");
		// TODO: Proper failed auth!
	}
}
