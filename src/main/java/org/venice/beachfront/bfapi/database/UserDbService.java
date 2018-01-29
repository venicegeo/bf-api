package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;

import org.venice.beachfront.bfapi.model.UserProfile;

public interface UserDbService {
	public void insertUser(String userId, String userName, String apiKey) throws SQLException;
	public UserProfile getUser(String userId) throws SQLException;
	public UserProfile getUserByApiKey(String apiKey) throws SQLException;
}
