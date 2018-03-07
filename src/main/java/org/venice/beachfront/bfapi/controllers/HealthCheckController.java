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

import java.util.HashMap;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.geoserver.GeoserverEnvironment;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.JobService;
import org.venice.beachfront.bfapi.services.PiazzaService;
import org.venice.beachfront.bfapi.services.UptimeService;

/**
 * Controller class for a simple health check endpoint.
 * 
 * @version 1.0
 */
@Controller
public class HealthCheckController {
	@Autowired
	private UptimeService uptimeService;
	@Autowired
	private PiazzaService piazzaService;
	@Autowired
	private JobService jobService;
	@Autowired
	private GeoserverEnvironment geoserverEnvironment;

	@RequestMapping(path = "/", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public Map<String, String> healthCheck() throws UserException {
		Map<String, String> healthCheckData = new HashMap<String, String>();
		// Show uptime
		healthCheckData.put("uptime", Double.toString(uptimeService.getUptimeSeconds()));
		healthCheckData.put("geoserver", geoserverEnvironment.getGeoServerBaseUrl());
		try {
			// Show algorithm Job Queue length as reported by Piazza
			for (Algorithm algorithm : piazzaService.getRegisteredAlgorithms()) {
				int jobCount = piazzaService.getAlgorithmStatistics(algorithm.getServiceId()).get("totalJobCount").asInt();
				healthCheckData.put(String.format("%s queued jobs", algorithm.getName()), Integer.toString(jobCount));
			}
			// Show outstanding Job length
			healthCheckData.put("jobs", Integer.toString(jobService.getOutstandingJobs().size()));
		} catch (UserException exception) {
			healthCheckData.put("error",
					String.format("There was an error retrieving Algorithm health check data: %s", exception.getMessage()));
		}
		return healthCheckData;
	}

}