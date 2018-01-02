package org.venice.beachfront.bfapi.services.impl;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.services.IABrokerService;
import org.venice.beachfront.bfapi.services.proto.IABrokerServiceProtoImpl;

@Profile("main")
@Service
public class IABrokerServiceImpl extends IABrokerServiceProtoImpl implements IABrokerService {
	// TODO: implement actual stuff
}
