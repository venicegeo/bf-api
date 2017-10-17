package org.venice.beachfront.bfapi.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class Confirmation {
	@JsonProperty("id") private String id;
	@JsonProperty("success") private boolean success;
	
	public Confirmation(String id, boolean success) {
		this.id = id;
		this.success = success;
	}
	
	public String getId() {
		return this.id;
	}
	
	public boolean getSuccess() {
		return this.success;
	}
}
