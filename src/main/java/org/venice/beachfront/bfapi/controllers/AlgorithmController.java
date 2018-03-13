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

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.AlgorithmService;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

/**
 * Main controller class for the retrieving information about available algorithms.
 * 
 * @version 1.0
 */
@Controller
public class AlgorithmController {
	@Autowired
	private AlgorithmService algorithmService;
	@Autowired
	private ObjectMapper objectMapper;

	@RequestMapping(path = "/algorithm", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public JsonNode getAllAlgorithms() throws UserException {
		List<Algorithm> algorithms = algorithmService.getAllAlgorithms();
		// Algorithms must be wrapped in a parent container
		ObjectNode container = objectMapper.createObjectNode();
		container.set("algorithms", objectMapper.convertValue(algorithms, JsonNode.class));
		return container;
	}

	@RequestMapping(path = "/algorithm/{id}", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public JsonNode getAlgorithmByServiceId(@PathVariable("id") String serviceId) throws UserException {
		Algorithm algorithm = algorithmService.getAlgorithm(serviceId);
		// Algorithm Wrapped in a parent container
		ObjectNode container = objectMapper.createObjectNode();
		container.set("algorithm", objectMapper.convertValue(algorithm, JsonNode.class));
		return container;
	}

}
