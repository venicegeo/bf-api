package org.venice.beachfront.bfapi.services;

import java.util.List;

import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.DetectionFeed;

import com.fasterxml.jackson.databind.JsonNode;

public interface DetectionFeedService {
	public DetectionFeed createDetectionFeed(
			String algorithmName, 
			String algorithmVersion, 
			DateTime expiresOn,
			int intervalSeconds, 
			String name, 
			JsonNode extras);
	
	public List<DetectionFeed> getDetectionFeeds();
	public DetectionFeed getDetectionFeed(String id);
	public Confirmation deleteDetectionFeed(String id);
}
