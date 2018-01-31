package org.venice.beachfront.bfapi.database.dao;

import javax.transaction.Transactional;

import org.springframework.data.repository.CrudRepository;
import org.venice.beachfront.bfapi.model.UserProfile;

@Transactional
public interface UserProfileDao extends CrudRepository<UserProfile, Long> {
	UserProfile findByUserId(String UserId);

	UserProfile findByApiKey(String ApiKey);
}
