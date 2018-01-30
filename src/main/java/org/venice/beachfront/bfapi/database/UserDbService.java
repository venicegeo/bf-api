package org.venice.beachfront.bfapi.database;

import java.sql.SQLException;

import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.DbDTO.UserEntry;

@Service
public class UserDbService {
	public void insertUser(String userId, String userName, String apiKey) throws SQLException {
		// TODO
	}

	public UserEntry getUser(String userId) throws SQLException {
		// TODO
		return null;
	}

	public UserEntry getUserByApiKey(String apiKey) throws SQLException {
		// TODO
		return null;
	}
}
