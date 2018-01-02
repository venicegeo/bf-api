package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;

import org.venice.beachfront.bfapi.database.DbDTO.UserEntry;

public interface UserDbService {
	public void insertUser(String userId, String userName, String apiKey) throws SQLException;
	public UserEntry getUser(String userId) throws SQLException;
	public UserEntry getUserByApiKey(String apiKey) throws SQLException;
}
