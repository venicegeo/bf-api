package org.venice.beachfront.bfapi.services;

import java.util.List;

import org.venice.beachfront.bfapi.model.Algorithm;

public interface AlgorithmService {
	public List<Algorithm> getAllAlgorithms();
	public Algorithm getAlgorithm(String serviceId);
}
