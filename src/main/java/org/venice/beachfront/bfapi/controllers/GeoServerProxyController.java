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
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.GeoServerProxyService;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import model.logger.Severity;
import util.PiazzaLogger;

/**
 * This controller will proxy WMS layer requests to the GeoServer instance.
 * 
 * @author Patrick.Doody
 *
 */
@Controller
@Api(value = "GeoServer")
public class GeoServerProxyController {
	@Autowired
	private PiazzaLogger piazzaLogger;
	@Autowired
	private GeoServerProxyService geoServerProxyService;

	@RequestMapping(path = "/geoserver/**")
	@ResponseBody
	@ApiOperation(value = "GeoServer Proxy", notes = "Proxies WMS requests to the GeoServer component", tags = "GeoServer")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "The proxied response"),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public ResponseEntity<byte[]> passthrough(HttpMethod method, HttpServletRequest request)
			throws IOException, URISyntaxException, UserException {
		if (!HttpMethod.GET.equals(method)) {
			piazzaLogger
					.log(String.format("Received invalid GeoServer proxy request for Method %s to URL %s. Only GET methods are supported.",
							method.toString(), request.getRequestURI()), Severity.INFORMATIONAL);
			throw new UserException("Invalid GeoServer proxy request. Only GET methods are supported.", HttpStatus.BAD_REQUEST);
		}
		piazzaLogger.log(
				String.format("Received GeoServer proxy request for Method %s to URL %s", method.toString(), request.getRequestURI()),
				Severity.INFORMATIONAL);
		return geoServerProxyService.proxyRequest(request);
	}
}
