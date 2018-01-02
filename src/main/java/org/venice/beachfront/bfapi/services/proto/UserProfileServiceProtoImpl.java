package org.venice.beachfront.bfapi.services.proto;

import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.UserProfileService;

public class UserProfileServiceProtoImpl implements UserProfileService {

	@Override
	public UserProfile getCurrentUserProfile() {
		return new UserProfile("user-profile-1", "User Name", "abc-api-key-123", DateTime.now().minusDays(1));
	}

}
