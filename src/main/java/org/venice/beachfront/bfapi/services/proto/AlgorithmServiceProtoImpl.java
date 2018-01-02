package org.venice.beachfront.bfapi.services.proto;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.services.AlgorithmService;

public class AlgorithmServiceProtoImpl implements AlgorithmService {
	private List<Algorithm> mockAlgorithms = new ArrayList<Algorithm>();
	
	public AlgorithmServiceProtoImpl() {
		this.mockAlgorithms.add(new Algorithm(
				"Alg1 description",
				"Alg1 interface",
				10,
				"Mock Algorithm 1",
				"mockAlg1",
				"1.0"));
		this.mockAlgorithms.add(new Algorithm(
				"Alg2 description",
				"Alg2 interface",
				20,
				"Mock Algorithm 2",
				"mockAlg2",
				"2.0"));
	}

	@Override
	public List<Algorithm> getAllAlgorithms() {
		return Collections.unmodifiableList(this.mockAlgorithms);
	}

	@Override
	public Algorithm getAlgorithm(String serviceId) {
		for (Algorithm a : this.mockAlgorithms) {
			if (a.getServiceId().equals(serviceId)) {
				return a;
			}
		}
		return null;
	}
}
