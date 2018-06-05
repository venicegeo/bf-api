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
package org.venice.beachfront.bfapi.geoserver;

import org.apache.tomcat.util.codec.binary.Base64;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;

@Component
@Profile({ "basic-geoserver-auth" })
public class BasicAuthHeaders extends HttpHeaders implements AuthHeaders {

	private static final long serialVersionUID = 1L;

	@Value("${vcap.services.pz-geoserver.credentials.boundless_geoserver_username}")
	private String geoserverUsername;
	@Value("${vcap.services.pz-geoserver.credentials.boundless_geoserver_password}")
	private String geoserverPassword;

	public HttpHeaders get() {

		// Get the Basic authentication Headers for GeoServer
		final String plainCredentials = String.format("%s:%s", geoserverUsername, geoserverPassword);
		final byte[] credentialBytes = plainCredentials.getBytes();
		final byte[] encodedCredentials = Base64.encodeBase64(credentialBytes);
		final String credentials = new String(encodedCredentials);
		add(HttpHeaders.AUTHORIZATION, "Basic " + credentials);

		return this;
	}
}