package org.venice.beachfront.bfapi.services.impl;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.services.DetectionFeedService;
import org.venice.beachfront.bfapi.services.proto.DetectionFeedServiceProtoImpl;

@Profile("main")
@Service
public class DetectionFeedServiceImpl extends DetectionFeedServiceProtoImpl implements DetectionFeedService {
	// TODO: implement actual stuff
}
