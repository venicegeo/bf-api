package org.venice.beachfront.bfapi.model;

import org.joda.time.DateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public class UserProfile {
	@JsonProperty("user_id") private final String id;
	@JsonProperty("name") private final String name;
	@JsonProperty("api_key") private final String apiKey;
	@JsonProperty("created_on") private final DateTime createdOn;
	
	public UserProfile(String id, String name, String apiKey, DateTime createdOn) {
		this.id = id;
		this.name = name;
		this.apiKey = apiKey;
		this.createdOn = createdOn;
	}

	public String getId() {
		return id;
	}

	public String getName() {
		return name;
	}

	public String getApiKey() {
		return apiKey;
	}

	public DateTime getCreatedOn() {
		return createdOn;
	}
}
