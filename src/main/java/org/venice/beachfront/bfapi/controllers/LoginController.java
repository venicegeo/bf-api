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

import javax.servlet.http.HttpServletRequest;

import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.servlet.view.RedirectView;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.UserProfileService;

/**
 * Main controller class for the handling user profiles.
 * 
 * @version 1.0
 */
@Controller
public class LoginController {
	@Autowired
	private UserProfileService userProfileService;
	@Value("${DOMAIN}")
	private String domain;

	@RequestMapping(path = "/login", method = RequestMethod.POST, produces = { "application/json" })
	@ResponseBody
	public RedirectView login(@JsonProperty(value = "userProfile") UserProfile userProfile) {
		// TODO: does the cookie need to be passed along/read from idam
		// TODO: Look at the user profile info from idam and put it in whatever format api needs
		RedirectView redirect = new RedirectView();
		redirect.setUrl(String.format("https://bf-ui.%s/", domain));
		return redirect;
	}

	@RequestMapping(path = "/login/geoaxis", method = RequestMethod.GET, produces = { "application/json" })
	@ResponseBody
	public RedirectView loginGeoaxis(HttpServletRequest request) {
		RedirectView redirect = new RedirectView();
		redirect.setUrl(
				String.format("https://pz-idam.%s/login/geoaxis", domain));
		return redirect;
	}

}
