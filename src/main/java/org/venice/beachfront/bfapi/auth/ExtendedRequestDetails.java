package org.venice.beachfront.bfapi.auth;

import javax.servlet.http.HttpServletRequest;

/**
 * Details that are attached to an Authorization request processed by the Provider. This allows us to inject information
 * into the authorize() call processed by that component, such as the HTTP Request information (cookies), that would not
 * normally be included in the default details object.
 * 
 * @author Patrick.Doody
 *
 */
public class ExtendedRequestDetails {

	private HttpServletRequest request;

	public ExtendedRequestDetails(HttpServletRequest request) {
		this.request = request;
	}

	/**
	 * Gets the Request Details
	 * 
	 * @return The request details.
	 */
	public HttpServletRequest getRequest() {
		return request;
	}
}