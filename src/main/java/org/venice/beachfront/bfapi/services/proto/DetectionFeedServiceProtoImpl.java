package org.venice.beachfront.bfapi.services.proto;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.joda.time.DateTime;
import org.venice.beachfront.bfapi.model.Confirmation;
import org.venice.beachfront.bfapi.model.DetectionFeed;
import org.venice.beachfront.bfapi.services.DetectionFeedService;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;

public class DetectionFeedServiceProtoImpl implements DetectionFeedService {
	private List<DetectionFeed> mockDetectionFeeds = new ArrayList<DetectionFeed>();
	private JsonNodeFactory jsonNodeFactory = new JsonNodeFactory(false);
	public DetectionFeedServiceProtoImpl() {
		this.mockDetectionFeeds.add(new DetectionFeed(
				"mock-df-1", 
				"mock-algo-1", 
				"1.0", 
				"created-by-1", 
				DateTime.now(), 
				DateTime.now().plusDays(1), 
				60, 
				"Mock Detection Feed 1", 
				null, 
				null, 
				Collections.emptyList(), 
				this.jsonNodeFactory.nullNode()));
		this.mockDetectionFeeds.add(new DetectionFeed(
				"mock-df-2", 
				"mock-algo-2", 
				"2.0", 
				"created-by-2", 
				DateTime.now(), 
				DateTime.now().plusDays(2), 
				120, 
				"Mock Detection Feed 2", 
				null, 
				null, 
				Collections.emptyList(), 
				this.jsonNodeFactory.nullNode()));
	}
	
	
	@Override
	public DetectionFeed createDetectionFeed(String algorithmName, String algorithmVersion, DateTime expiresOn,
			int intervalSeconds, String name, JsonNode extras) {
		// TODO Auto-generated method stub
		return new DetectionFeed(
				"detection-feed-1", 
				algorithmName, 
				algorithmVersion, 
				"created-by-id", 
				DateTime.now(), 
				expiresOn, 
				intervalSeconds, 
				algorithmName, 
				null, 
				null, 
				Collections.emptyList(), 
				extras);
	}

	@Override
	public List<DetectionFeed> getDetectionFeeds() {
		return Collections.unmodifiableList(this.mockDetectionFeeds);
	}

	@Override
	public DetectionFeed getDetectionFeed(String id) {
		for (DetectionFeed df : this.mockDetectionFeeds) {
			if (df.getId().equals(id)) {
				return df;
			}
		}
		return null;
	}

	@Override
	public Confirmation deleteDetectionFeed(String id) {
		return new Confirmation(id, true);
	}

}
