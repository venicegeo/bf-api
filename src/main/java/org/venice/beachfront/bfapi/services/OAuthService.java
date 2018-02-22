package org.venice.beachfront.bfapi.services;

import java.nio.charset.Charset;
import java.util.Base64;
import java.util.UUID;

import org.joda.time.DateTime;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.oauth.AccessTokenRequestBody;
import org.venice.beachfront.bfapi.model.oauth.AccessTokenResponseBody;
import org.venice.beachfront.bfapi.model.oauth.ProfileResponseBody;

@Service
public class OAuthService {
	@Value("${DOMAIN}")
	private String domain;

	@Value("${oauth.token-url}")
	private String oauthTokenUrl;

	@Value("${oauth.profile-url")
	private String oauthProfileUrl;

	@Value("${OAUTH_CLIENT_ID}")
	private String oauthClientId;

	@Value("${OAUTH_SECRET}")
	private String oauthClientSecret;

	@Autowired
	private RestTemplate restTemplate;

	@Autowired
	private UserProfileService userProfileService;

	public String getOauthRedirectUri() {
		return UriComponentsBuilder.newInstance().host("bf-api." + this.domain).pathSegment("login").build().toUri().toString();
	}

	public String requestAccessToken(String authCode) throws UserException {
		AccessTokenRequestBody body = new AccessTokenRequestBody("authorization_code", authCode, this.getOauthRedirectUri());
		HttpHeaders headers = new HttpHeaders();
		headers.set("Authorization", this.createTokenAuthHeader());
		HttpEntity<AccessTokenRequestBody> entity = new HttpEntity<>(body, headers);

		ResponseEntity<AccessTokenResponseBody> response;
		try {
			response = this.restTemplate.exchange(this.oauthTokenUrl, HttpMethod.POST, entity, AccessTokenResponseBody.class);
		} catch (RestClientResponseException ex) {
			int code = ex.getRawStatusCode(); 
			if (code >= 400 && code <= 499) {
				throw new UserException("Unauthorized: Failed to acquire OAuth access token from access code", ex, HttpStatus.valueOf(code));
			}
			if (code >= 500 && code <= 599) {
				throw new UserException("Upstream OAuth error acquiring OAuth access token from access code", ex, ex.getResponseBodyAsString(), HttpStatus.BAD_GATEWAY);
			}
			throw new UserException("Unknown error acquiring OAuth access token from access code", ex, ex.getResponseBodyAsString(), HttpStatus.INTERNAL_SERVER_ERROR);
		}

		return response.getBody().getAccessToken();
	}

	public ProfileResponseBody requestOAuthProfile(String accessToken) throws UserException {
		HttpHeaders headers = new HttpHeaders();
		headers.set("Authorization", "Bearer " + accessToken);
		HttpEntity<Object> entity = new HttpEntity<>(null, headers);

		ResponseEntity<ProfileResponseBody> response;
		try {
			response = this.restTemplate.exchange(this.oauthProfileUrl, HttpMethod.GET, entity, ProfileResponseBody.class);
		} catch (RestClientResponseException ex) {
			int code = ex.getRawStatusCode(); 
			if (code >= 400 && code <= 499) {
				throw new UserException("Unauthorized: Failed to acquire user profile", ex, HttpStatus.valueOf(code));
			}
			if (code >= 500 && code <= 599) {
				throw new UserException("Upstream acquiring user profile", ex, ex.getResponseBodyAsString(), HttpStatus.BAD_GATEWAY);
			}
			throw new UserException("Unknown error acquiring user profile", ex, ex.getResponseBodyAsString(), HttpStatus.INTERNAL_SERVER_ERROR);
		}

		return response.getBody();
	}

	public UserProfile getOrCreateUser(String userId, String userName) {
		UserProfile user = userProfileService.getUserProfileById(userId);
		if (user != null) {
			// Check if the user has a current API Key
			if (user.getApiKey() == null) {
				// Generate a new API Key if the user exists, but has no existing key
				user.setApiKey(generateApiKey());
				userProfileService.updateLastAccessed(user);
			}
			return user;
		}

		String apiKey = generateApiKey();
		user = new UserProfile(userId, userName, apiKey, DateTime.now());
		userProfileService.saveUserProfile(user);
		return user;
	}

	private String generateApiKey() {
		return UUID.randomUUID().toString();
	}

	private String createTokenAuthHeader() {
		String auth = this.oauthClientId + ":" + this.oauthClientSecret;
		byte[] encodedAuth = Base64.getEncoder().encode(auth.getBytes(Charset.forName("US-ASCII")));
		return "Basic " + new String(encodedAuth);
	}
}
