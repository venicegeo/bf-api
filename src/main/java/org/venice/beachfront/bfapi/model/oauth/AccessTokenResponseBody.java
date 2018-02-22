package org.venice.beachfront.bfapi.model.oauth;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AccessTokenResponseBody {
	@JsonProperty("access_token")
	private String accessToken;

	public AccessTokenResponseBody() {
		super();
	}
	
	public AccessTokenResponseBody(String accessToken) {
		super();
		this.accessToken = accessToken;
	}
	
	public String getAccessToken() {
		return accessToken;
	}
}
