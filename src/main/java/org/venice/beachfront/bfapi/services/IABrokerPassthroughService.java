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

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

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

	public ResponseEntity<byte[]> passthroughRequest(String uri, String body, HttpMethod method, HttpServletRequest request)
			throws MalformedURLException, IOException, URISyntaxException {
		URI iaURI = new URI(IA_BROKER_PROTOCOL, null, IA_BROKER_SERVER, IA_BROKER_PORT, request.getRequestURI(), request.getQueryString(),
				null);
		return restTemplate.exchange(iaURI, method, new HttpEntity<String>(body), byte[].class);
	}
}
