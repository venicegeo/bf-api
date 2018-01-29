package org.venice.beachfront.bfapi.database.impl;

import java.sql.SQLException;

import com.vividsolutions.jts.geom.Geometry;
import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.DbDTO;
import org.venice.beachfront.bfapi.database.SceneDbService;
import org.venice.beachfront.bfapi.database.UserDbService;
import org.venice.beachfront.bfapi.database.dao.SceneDao;
import org.venice.beachfront.bfapi.database.dao.UserProfileDao;
import org.venice.beachfront.bfapi.model.Scene;
import org.venice.beachfront.bfapi.model.UserProfile;

@Service
public class UserDbServiceImpl implements UserDbService {
	@Autowired
	private UserProfileDao userProfileDao;

	@Override
	public void insertUser(String userId, String userName, String apiKey) throws SQLException {
		userProfileDao.save(new UserProfile(
				userId,
				userName,
				apiKey,
				DateTime.now()
		));
	}

	@Override
	public UserProfile getUser(String userId) throws SQLException {
		return userProfileDao.findByUserId(userId);
	}

	@Override
	public UserProfile getUserByApiKey(String apiKey) throws SQLException {
		return userProfileDao.findByApiKey(apiKey);
	}
}
