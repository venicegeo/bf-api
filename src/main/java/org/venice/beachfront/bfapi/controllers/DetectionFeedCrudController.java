package org.venice.beachfront.bfapi.controllers;

import java.util.List;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.DetectionFeed;
import org.venice.beachfront.bfapi.services.DetectionFeedService;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * Main controller class for the Detection Feed CRUD endpoints.
 * 
 * @version 1.0
 */
public class DetectionFeedCrudController {
	private final DetectionFeedService detectionFeedService;
	
	@Autowired
	public DetectionFeedCrudController(DetectionFeedService detectionFeedService) {
		this.detectionFeedService = detectionFeedService;
	}

	@RequestMapping(
			path="/feed",
			method=RequestMethod.POST,
			consumes={"application/json"},
			produces={"application/json"})
	@ResponseBody
	public DetectionFeed createDetectionFeed(@RequestBody CreateDetectionFeedBody body) {
		return this.detectionFeedService.createDetectionFeed(
				body.algorithmName, 
				body.algorithmVersion, 
				body.expiresOn, 
				body.intervalSeconds, 
				body.name, 
				body.extras);
	}
	
	@RequestMapping(
	        path="/feed",
	        method=RequestMethod.GET,
	        produces={"application/json"})
	@ResponseBody
	public List<DetectionFeed> listDetectionFeeds() {
		return this.detectionFeedService.getDetectionFeeds();
	}
	
	@RequestMapping(
			path="/feed/{id}",
			method=RequestMethod.GET,
			produces={"application/json"})
	@ResponseBody
	public DetectionFeed getDetectionFeedById(@PathVariable("id") String id) {
		return this.detectionFeedService.getDetectionFeed(id);
	}
	
	@RequestMapping(
			path="/feed/{id}",
			method=RequestMethod.DELETE,
			produces={"application/json"})
	@ResponseBody
	public Confirmation deleteDetectionFeed(@PathVariable("id") String id) {
		return this.detectionFeedService.deleteDetectionFeed(id);
	}

	private static class CreateDetectionFeedBody {
		public final String algorithmName;
		public final String algorithmVersion;
		public final DateTime expiresOn;
		public final int intervalSeconds;
		public final String name;
		public final JsonNode extras;
		
		@JsonCreator
		public CreateDetectionFeedBody(
				@JsonProperty(value="algorithm_name", required=true) String algorithmName, 
				@JsonProperty(value="algorithm_version", required=true) String algorithmVersion, 
				@JsonProperty(value="expires_on", required=true) DateTime expiresOn,
				@JsonProperty(value="interval", required=true) int intervalSeconds, 
				@JsonProperty(value="name", required=true) String name, 
				@JsonProperty(value="extras", required=true) JsonNode extras) {
			this.algorithmName = algorithmName;
			this.algorithmVersion = algorithmVersion;
			this.expiresOn = expiresOn;
			this.intervalSeconds = intervalSeconds;
			this.name = name;
			this.extras = extras;
		}

		
	}

}
