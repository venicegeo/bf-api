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
package org.venice.beachfront.bfapi.services;

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.net.URLDecoder;

import javax.servlet.http.HttpServletRequest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import org.venice.beachfront.bfapi.geoserver.AuthHeaders;
import org.venice.beachfront.bfapi.geoserver.GeoserverEnvironment;
import org.venice.beachfront.bfapi.model.exception.UserException;

import model.logger.Severity;
import util.PiazzaLogger;

/**
 * Service that proxies requests to the GeoServer instance
 */
@Service
public class GeoServerProxyService {
	@Autowired
	private RestTemplate restTemplate;
	@Autowired
	private PiazzaLogger piazzaLogger;
	@Autowired
	private GeoserverEnvironment geoserverEnvironment;
	@Autowired
	private AuthHeaders authHeaders;

	public ResponseEntity<byte[]> proxyRequest(HttpServletRequest request)
			throws MalformedURLException, IOException, URISyntaxException, UserException {
		String requestPath = request.getRequestURI();
		// Form the complete URI by piecing together the GeoServer URL with the API proxy request parameters
		URL geoserverUrl = new URL(geoserverEnvironment.getGeoServerBaseUrl());
		URI requestUri = new URI(geoserverUrl.getProtocol(), null, geoserverUrl.getHost(), geoserverUrl.getPort(), requestPath,
				request.getQueryString(), null);
		// Double encoding takes place here. First, in the REST Request delivered to API by the client. Second, in the
		// translation to the URI object. Decode both of these steps to get the real, completely decoded request to
		// GeoServer.
		String decodedUrl = URLDecoder.decode(requestUri.toString(), "UTF-8");
		decodedUrl = URLDecoder.decode(decodedUrl.toString(), "UTF-8");
		piazzaLogger.log(String.format("Proxying request to GET GeoServer at URI %s", decodedUrl), Severity.INFORMATIONAL);
		try {
			HttpEntity<String> requestHeaders = new HttpEntity<>(authHeaders.get());
			ResponseEntity<byte[]> response = restTemplate.exchange(decodedUrl, HttpMethod.GET, requestHeaders, byte[].class);
			return response;
		} catch (HttpClientErrorException | HttpServerErrorException exception) {
			piazzaLogger.log(String.format("Received GeoServer error response, code=%d, length=%d, for URI %s",
					exception.getStatusCode().value(), exception.getResponseBodyAsString().length(), requestUri.toString()),
					Severity.ERROR);
			if (exception.getStatusCode().equals(HttpStatus.UNAUTHORIZED) || exception.getStatusCode().equals(HttpStatus.FORBIDDEN)) {
				throw new UserException("Bad Authentication with GeoServer", exception, exception.getResponseBodyAsString(),
						HttpStatus.BAD_REQUEST);
			}
			throw new UserException("Upstream GeoServer error", exception, exception.getResponseBodyAsString(), exception.getStatusCode());
		}
	}
}
