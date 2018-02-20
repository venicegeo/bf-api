package org.venice.beachfront.bfapi.services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.UserProfileDao;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;

@Service
public class UserProfileService {
	@Autowired
	UserProfileDao userProfileDao;

	public UserProfile getCurrentUserProfile() {
		return null;
	}

	public UserProfile getUserProfileById(String userId) {
		return userProfileDao.findByUserId(userId);
	}

	public UserProfile getUserProfileByApiKey(String apiKey) {
		return userProfileDao.findByApiKey(apiKey);
	}

	/**
	 * Returns the UserProfile object from the Authentication token returned by the Auth provider
	 * 
	 * @param authentication
	 *            Authentication token object
	 * @return User Profile
	 */
	public UserProfile getProfileFromAuthentication(Authentication authentication) throws UserException {
		try {
			return (UserProfile) (authentication.getPrincipal());
		} catch (Exception exception) {
			throw new UserException("Error getting the User Profile object from the specified Key.", exception,
					HttpStatus.INTERNAL_SERVER_ERROR);
		}
	}
}
