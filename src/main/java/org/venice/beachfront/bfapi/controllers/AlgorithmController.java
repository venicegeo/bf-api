package org.venice.beachfront.bfapi.controllers;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.Algorithm;
import org.venice.beachfront.bfapi.services.AlgorithmService;

/**
 * Main controller class for the retrieving information about available algorithms.
 * 
 * @version 1.0
 */
@Controller
public class AlgorithmController {
	private AlgorithmService algorithmsService;

	@Autowired
	public AlgorithmController(AlgorithmService service) {
		this.algorithmsService = service;
	}
	
	@RequestMapping(
			path="/algorithms",
			method=RequestMethod.GET,
			produces={"application/json"})
	@ResponseBody
	public List<Algorithm> getAllAlgorithms() {
		return this.algorithmsService.getAllAlgorithms();
	}
	
	@RequestMapping(
			path="/algorithms/{id}",
			method=RequestMethod.GET,
			produces={"application/json"})
	@ResponseBody
	public Algorithm getAlgorithmByServiceId(@PathVariable("id") String serviceId) {
		return this.algorithmsService.getAlgorithm(serviceId);
	}

}
