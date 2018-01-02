package org.venice.beachfront.bfapi.services.impl;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.services.AlgorithmService;
import org.venice.beachfront.bfapi.services.proto.AlgorithmServiceProtoImpl;

@Profile("main")
@Service
public class AlgorithmServiceImpl extends AlgorithmServiceProtoImpl implements AlgorithmService {
	// TODO: implement actual stuff
}
