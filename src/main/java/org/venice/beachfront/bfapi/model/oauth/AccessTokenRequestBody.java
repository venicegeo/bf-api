package org.venice.beachfront.bfapi.model.oauth;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AccessTokenRequestBody {
	@JsonProperty("grant_type")
	private final String grantType;
	
	@JsonProperty("code")
	private final String code;
	
	@JsonProperty("redirect_uri")
	private final String redirectUri;
	
	public AccessTokenRequestBody(String grantType, String code, String redirectUri) {
		this.grantType = grantType;
		this.code = code;
		this.redirectUri = redirectUri;
	}

	public String getGrantType() {
		return grantType;
	}

	public String getCode() {
		return code;
	}
	
	public String getRedirectUri() {
		return redirectUri;
	}
}