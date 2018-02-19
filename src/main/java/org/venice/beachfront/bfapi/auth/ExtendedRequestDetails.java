package org.venice.beachfront.bfapi.auth;

import javax.servlet.http.HttpServletRequest;

/**
 * Providing a way to pass Servlet Request details directly into the Auth providers so all headers can be parsed
 * individually as needed.
 */
public class ExtendedRequestDetails {
	private HttpServletRequest request;

	public ExtendedRequestDetails(HttpServletRequest request) {
		this.request = request;
	}

	public HttpServletRequest getRequest() {
		return request;
	}
}