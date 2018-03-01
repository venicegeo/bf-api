package org.venice.beachfront.bfapi.model.oauth;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AccessTokenRequestBody {
	@JsonProperty("grant_type")
	private String grantType;

	@JsonProperty("code")
	private String code;

	@JsonProperty("redirect_uri")
	private String redirectUri;

	public AccessTokenRequestBody() {
		super();
	}

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