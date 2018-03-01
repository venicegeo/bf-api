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
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.FormHttpMessageConverter;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.oauth.AccessTokenResponseBody;
import org.venice.beachfront.bfapi.model.oauth.ProfileResponseBody;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import model.logger.Severity;
import util.PiazzaLogger;

@Service
public class OAuthService {
	@Value("${DOMAIN}")
	private String domain;
	@Value("${oauth.token-url}")
	private String oauthTokenUrl;
	@Value("${oauth.profile-url}")
	private String oauthProfileUrl;
	@Value("${OAUTH_CLIENT_ID}")
	private String oauthClientId;
	@Value("${OAUTH_SECRET}")
	private String oauthClientSecret;

	@Autowired
	private RestTemplate restTemplate;
	@Autowired
	private UserProfileService userProfileService;
	@Autowired
	private PiazzaLogger piazzaLogger;

	public String getOauthRedirectUri() {
		// TODO: should this be a configuration variable, since it needs to match 100% with the oauth provider config?
		return UriComponentsBuilder.newInstance().scheme("https").host("bf-api." + this.domain).pathSegment("login").build().toUri()
				.toString();
	}

	public String requestAccessToken(String authCode) throws UserException {
		MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
		body.add("grant_type", "authorization_code");
		body.add("redirect_uri", this.getOauthRedirectUri());
		body.add("code", authCode);

		HttpHeaders headers = new HttpHeaders();
		headers.set("Authorization", this.createTokenAuthHeader());
		headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
		HttpEntity<MultiValueMap<String, String>> entity = new HttpEntity<>(body, headers);

		restTemplate.getMessageConverters().add(new FormHttpMessageConverter());
		restTemplate.getMessageConverters().add(new MappingJackson2HttpMessageConverter());

		ResponseEntity<AccessTokenResponseBody> response;
		try {
			response = this.restTemplate.exchange(this.oauthTokenUrl, HttpMethod.POST, entity, AccessTokenResponseBody.class);
		} catch (RestClientResponseException ex) {
			piazzaLogger.log(String.format("Failed call to OAuth Token URL with Status %s and error %s", ex.getStatusText(),
					ex.getResponseBodyAsString()), Severity.ERROR);
			int code = ex.getRawStatusCode();
			if (code >= 400 && code <= 499) {
				throw new UserException("Unauthorized: Failed to acquire OAuth access token from access code", ex,
						HttpStatus.valueOf(code));
			} else {
				String message = String.format("Upstream server error acquiring OAuth access token from access code; upstream code=%d",
						code);
				throw new UserException(message, ex, ex.getResponseBodyAsString(), HttpStatus.BAD_GATEWAY);
			}
		}

		piazzaLogger.log("Successfully retrieved access token for OAuth Token Request.", Severity.INFORMATIONAL);
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
			piazzaLogger.log(String.format("Failed call to OAuth Profile URL with Status %s and error %s", ex.getStatusText(),
					ex.getResponseBodyAsString()), Severity.ERROR);
			int code = ex.getRawStatusCode();
			if (code >= 400 && code <= 499) {
				throw new UserException("Unauthorized: Failed to acquire user profile", ex, HttpStatus.valueOf(code));
			} else {
				String message = String.format("Upstream server error acquiring user profile; upstream code=%d", code);
				throw new UserException(message, ex, ex.getResponseBodyAsString(), HttpStatus.BAD_GATEWAY);
			}
		}

		piazzaLogger.log("Successfully retrieved profile for OAuth Profile Request.", Severity.INFORMATIONAL);
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
			piazzaLogger.log(String.format("Returning User %s with Name %s has successfully logged in.", userId, userName),
					Severity.INFORMATIONAL);
			return user;
		}

		String apiKey = generateApiKey();
		user = new UserProfile(userId, userName, apiKey, DateTime.now());
		userProfileService.saveUserProfile(user);
		piazzaLogger.log(String.format("Successful first time login for User %s with Name %s. This User's Profile has been created.",
				userId, userName), Severity.INFORMATIONAL);
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
