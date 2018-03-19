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

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.Job;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.UserProfileService;

import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiResponse;
import io.swagger.annotations.ApiResponses;
import model.logger.Severity;
import util.PiazzaLogger;

/**
 * Main controller class for the handling user profiles.
 * 
 * @version 1.0
 */
@Controller
@Api(value = "Profile")
public class UserProfileController {
	@Autowired
	private UserProfileService userProfileService;
	@Autowired
	private PiazzaLogger piazzaLogger;

	@RequestMapping(path = "/user", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	@ApiOperation(value = "Get User Profile Information", notes = "Returns information on the current User Profile", tags = "Profile")
	@ApiResponses(value = { @ApiResponse(code = 200, message = "The Job information", response = Job.class),
			@ApiResponse(code = 401, message = "Unauthorized API Key", response = UserProfile.class),
			@ApiResponse(code = 404, message = "User not found", response = String.class),
			@ApiResponse(code = 500, message = "Unexpected internal server error", response = String.class) })
	public UserProfile getCurrentUserProfile(Authentication authentication) throws UserException {
		UserProfile currentUser = userProfileService.getProfileFromAuthentication(authentication);
		if (currentUser != null) {
			piazzaLogger.log(String.format("User %s requested their User profile information.", currentUser.getUserId()),
					Severity.INFORMATIONAL);
			return currentUser;
		} else {
			throw new UserException("User Profile not found for specified API Key.", HttpStatus.UNAUTHORIZED);
		}
	}

}
