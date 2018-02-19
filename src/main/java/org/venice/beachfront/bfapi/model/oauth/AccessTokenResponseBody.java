package org.venice.beachfront.bfapi.model.oauth;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AccessTokenResponseBody {
	@JsonProperty("grant_type")
	private final String accessToken;

	public AccessTokenResponseBody(String accessToken) {
		super();
		this.accessToken = accessToken;
	}
	public String getAccessToken() {
		return accessToken;
	}
}
