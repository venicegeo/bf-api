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