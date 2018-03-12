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
package org.venice.beachfront.bfapi.controllers;

import java.io.IOException;
import java.net.URISyntaxException;

import javax.servlet.http.HttpServletRequest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.services.IABrokerPassthroughService;

import model.logger.Severity;
import util.PiazzaLogger;

/**
 * Main controller class for the passthrough to bf-ia-broker.
 * 
 * @version 1.0
 */
@Controller
public class IABrokerPassthroughController {
	@Autowired
	private IABrokerPassthroughService iaBrokerPassthroughService;
	@Autowired
	private PiazzaLogger piazzaLogger;

	@RequestMapping(path = "/ia/**")
	@ResponseBody
	public ResponseEntity<byte[]> passthrough(HttpMethod method, HttpServletRequest request) throws IOException, URISyntaxException {
		piazzaLogger.log(
				String.format("Received IA-broker passthrough request for Method %s to URL %s", method.toString(), request.getRequestURI()),
				Severity.INFORMATIONAL);
		return iaBrokerPassthroughService.passthroughRequest(method, request);
	}
}
