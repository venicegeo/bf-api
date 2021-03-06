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

import java.net.URI;
import java.net.URISyntaxException;
import java.util.concurrent.CompletableFuture;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.SceneService;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;

/**
 * Main controller class for managing and downloading scenes.
 * 
 * @version 1.0
 */
@Controller
@Api(value = "Scene")
public class SceneController {
	@Autowired
	private SceneService iaBrokerService;

	@RequestMapping(path = "/scene/{id}/download", method = RequestMethod.GET, params = { "planet_api_key" })
	@ResponseBody
	@ApiOperation(value = "Download Scene Imagery", notes = "Downloads the raw scene imagery for the specified Scene", tags = "Scene")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "Scene Bytes", response = byte[].class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = String.class),
			@ApiResponse(code = 404, message = "Scene not found", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public CompletableFuture<ResponseEntity<?>> downloadScene(
			@ApiParam(value = "ID of the Scene", required = true) @PathVariable(value = "id") String sceneId,
			@RequestParam(value = "planet_api_key", required = true) String planetApiKey) throws UserException {
		return this.iaBrokerService.asyncGetActiveScene(sceneId, planetApiKey, true).thenApply((Scene activeScene) -> {
			HttpHeaders headers = new HttpHeaders();
			try {
				headers.setLocation(new URI(activeScene.getUri()));
			} catch (URISyntaxException e) {
				throw new RuntimeException(e);
			}
			return ResponseEntity.status(HttpStatus.FOUND).headers(headers).build();
		});
	}
}
