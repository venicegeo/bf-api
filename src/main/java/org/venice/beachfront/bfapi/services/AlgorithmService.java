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
