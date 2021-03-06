/**
 * Copyright 2018, Radiant Solutions, Inc.
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
package org.venice.beachfront.bfapi.services;

import java.util.Arrays;

import javax.annotation.PostConstruct;

import org.joda.time.DateTime;
import org.joda.time.Minutes;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.core.env.Environment;
import org.springframework.http.HttpStatus;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.database.dao.UserProfileDao;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;

import model.logger.Severity;
import util.PiazzaLogger;

@Service
@EnableScheduling
public class UserProfileService {
	@Value("${api.key.timeout.minutes}")
	private int API_KEY_TIMEOUT_MINUTES;

	@Autowired
	UserProfileDao userProfileDao;
	@Autowired
	private PiazzaLogger piazzaLogger;
	@Autowired
	private Environment environment;

	@PostConstruct
	public void initializeAnonymousUser() {
		if (Arrays.asList(environment.getActiveProfiles()).contains("insecure")) {
			piazzaLogger.log("Insecure profile detected. Verifying Mock User in database.", Severity.INFORMATIONAL);
			// In the case of insecure profile, initialize the Test User profile.
			UserProfile mockProfile = getMockProfile();
			if (getUserProfileById(mockProfile.getUserId()) == null) {
				piazzaLogger.log("Inserting Mock User into database.", Severity.INFORMATIONAL);
				saveUserProfile(getMockProfile());
			}
			piazzaLogger.log("Mock User initialized.", Severity.INFORMATIONAL);
		}
	}

	public void saveUserProfile(UserProfile userProfile) {
		userProfileDao.save(userProfile);
	}

	public UserProfile getUserProfileById(String userId) {
		return userProfileDao.findByUserId(userId);
	}

	public UserProfile getUserProfileByApiKey(String apiKey) {
		return userProfileDao.findByApiKey(apiKey);
	}

	public void updateLastAccessed(UserProfile userProfile) {
		userProfile.setLastAccessed(new DateTime());
		userProfileDao.save(userProfile);
	}

	/**
	 * Invalidates the API Key for the specified User Profile. This profile will need to generate a new key to login.
	 */
	public void invalidateKey(UserProfile userProfile) {
		userProfile.setApiKey(null);
		userProfileDao.save(userProfile);
		piazzaLogger.log(String.format("Invalidating API Key for User %s", userProfile.getUserId()), Severity.INFORMATIONAL);
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
			if (Arrays.asList(environment.getActiveProfiles()).contains("insecure")) {
				// Return a Mock object in the case when the secure profile is disabled. Testing purposes.
				return getMockProfile();
			} else {
				// Return the Profile
				return (UserProfile) (authentication.getPrincipal());
			}
		} catch (Exception exception) {
			throw new UserException("Error getting the User Profile object from the specified Key.", exception,
					HttpStatus.INTERNAL_SERVER_ERROR);
		}
	}

	/**
	 * Every 5 minutes, scan for expired API Keys that have not been used recently. Invalidate these keys if they are
	 * older than the threshold.
	 */
	@Scheduled(fixedDelay = 300000, initialDelay = 60000)
	public void reapExpiredApiKeys() {
		piazzaLogger.log("Performing Periodic Reaping of Expired API Keys", Severity.INFORMATIONAL);
		for (UserProfile userProfile : userProfileDao.findAll()) {
			// Check the last Access time and compare it with the threshold
			if (userProfile.getApiKey() != null) {
				// If the account has never been accessed, set the last access time to the creation time (Legacy)
				if (userProfile.getLastAccessed() == null) {
					userProfile.setLastAccessed(userProfile.getCreatedOn());
					saveUserProfile(userProfile);
				}
				if (Minutes.minutesBetween(userProfile.getLastAccessed(), new DateTime()).getMinutes() >= API_KEY_TIMEOUT_MINUTES) {
					// Expire the Key
					piazzaLogger.log(String.format("Server-side timeout of key for user %s due to inactivity.", userProfile.getName()),
							Severity.INFORMATIONAL);
					this.invalidateKey(userProfile);
				}
			}
		}
	}

	/**
	 * Used for testing purposes. Generates a mock profile.
	 */
	private UserProfile getMockProfile() {
		return new UserProfile("Test User", "Test User", "Test Key", new DateTime());
	}
}
