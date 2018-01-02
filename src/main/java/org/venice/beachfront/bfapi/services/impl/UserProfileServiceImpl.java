package org.venice.beachfront.bfapi.services.impl;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.services.UserProfileService;
import org.venice.beachfront.bfapi.services.proto.UserProfileServiceProtoImpl;

@Profile("main")
@Service
public class UserProfileServiceImpl extends UserProfileServiceProtoImpl implements UserProfileService {
	// TODO: implement actual stuff
}
