/**
 * Copyright 2016, RadiantBlue Technologies, Inc.
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

import javax.servlet.http.HttpServletRequest;

import org.apache.commons.io.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import model.logger.Severity;
import util.PiazzaLogger;

/**
 * Service that proxies all requests to the IA Broker
 */
@Service
public class IABrokerPassthroughService {
	@Value("${ia.broker.protocol}")
	private String IA_BROKER_PROTOCOL;
	@Value("${ia.broker.server}")
	private String IA_BROKER_SERVER;
	@Value("${ia.broker.port}")
	private Integer IA_BROKER_PORT;
	@Autowired
	private RestTemplate restTemplate;
	@Autowired
	private PiazzaLogger piazzaLogger;

	public ResponseEntity<byte[]> passthroughRequest(HttpMethod method, HttpServletRequest request)
			throws MalformedURLException, IOException, URISyntaxException {
		// URI to ia-Broker will strip out the /ia prefix that the bf-api uses to denote ia-broker proxying
		URI uri = new URI(IA_BROKER_PROTOCOL, null, IA_BROKER_SERVER, IA_BROKER_PORT, request.getRequestURI().substring("/ia".length()),
				request.getQueryString(), null);
		String body = IOUtils.toString(request.getReader());
		piazzaLogger.log(String.format("Proxying request to IA Broker at URI %s", uri.toString()), Severity.INFORMATIONAL);
		return restTemplate.exchange(uri, method, new HttpEntity<String>(body), byte[].class);
	}
}
