package org.venice.beachfront.bfapi.services;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.UserProfileDao;
import org.venice.beachfront.bfapi.model.UserProfile;

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
}
