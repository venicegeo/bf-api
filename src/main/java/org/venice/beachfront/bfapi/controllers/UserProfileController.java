package org.venice.beachfront.bfapi.controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.UserProfileService;

/**
 * Main controller class for the handling user profiles.
 * 
 * @version 1.0
 */
@Controller
public class UserProfileController {
	private UserProfileService userProfileService;
	
	@Autowired
	public UserProfileController(UserProfileService userProfileService) {
		this.userProfileService = userProfileService;
	}
	
	@RequestMapping(
			path="/profile/me",
			method=RequestMethod.GET,
			produces={"application/json"})
	@ResponseBody
	public UserProfile getCurrentUserProfile() {
		return this.userProfileService.getCurrentUserProfile();
	}
	
}
