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
package org.venice.beachfront.bfapi.controllers;

import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;

/**
 * Main controller class for the handling user profiles.
 * 
 * @version 1.0
 */
@Controller
public class UserProfileController {
	@RequestMapping(path = "/user", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public UserProfile getCurrentUserProfile(Authentication authentication) throws UserException {
		UserProfile currentUser = (UserProfile) authentication.getPrincipal();
		if (currentUser != null) {
			return currentUser;
		} else {
			throw new UserException("User Profile not found for specified API Key.", HttpStatus.UNAUTHORIZED);
		}
	}

}
