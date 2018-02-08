package org.venice.beachfront.bfapi.services;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.model.exception.UserException;

@Service
public class AlgorithmService {
	@Autowired
	private PiazzaService piazzaService;

	public List<Algorithm> getAllAlgorithms() throws UserException {
		return piazzaService.getRegisteredAlgorithms();
	}

	public Algorithm getAlgorithm(String serviceId) throws UserException {
		return piazzaService.getRegisteredAlgorithm(serviceId);
	}
}
