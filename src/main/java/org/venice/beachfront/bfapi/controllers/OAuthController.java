/**
 * Copyright 2018, Radiant Solutions, Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
package org.venice.beachfront.bfapi.controllers;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.util.UriComponentsBuilder;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.oauth.ProfileResponseBody;
import org.venice.beachfront.bfapi.services.OAuthService;
import org.venice.beachfront.bfapi.services.UserProfileService;

import model.logger.AuditElement;
import model.logger.Severity;
import util.PiazzaLogger;

@Controller
public class OAuthController {
	@Value("${DOMAIN}")
	private String domain;
	@Value("${oauth.authorize-url}")
	private String oauthAuthorizeUrl;
	@Value("${oauth.logout-url}")
	private String oauthLogoutUrl;
	@Value("${OAUTH_CLIENT_ID}")
	private String oauthClientId;
	@Value("${cookie.expiry.seconds}")
	private int COOKIE_EXPIRY_SECONDS;
	@Value("${cookie.name}")
	private String COOKIE_NAME;

	@Autowired
	private OAuthService oauthService;
	@Autowired
	private PiazzaLogger piazzaLogger;

	@Autowired
	private UserProfileService userProfileService;

	@RequestMapping(path = "/oauth/start", method = RequestMethod.GET, produces = { "text/plain" })
	@ResponseBody
	public String oauthStartExchange(HttpServletResponse response) {
		String callbackRedirectUri = this.oauthService.getOauthRedirectUri();

		String redirectUri = UriComponentsBuilder.fromHttpUrl(this.oauthAuthorizeUrl).queryParam("client_id", this.oauthClientId)
				.queryParam("redirect_uri", callbackRedirectUri).queryParam("response_type", "code").queryParam("scope", "UserProfile.me")
				.build().toUri().toString();

		response.setStatus(HttpStatus.FOUND.value());
		response.setHeader("Location", redirectUri);
		return "Redirecting to oauth provider...";
	}

	@RequestMapping(path = "/oauth/callback", method = RequestMethod.GET, produces = { "text/plain" })
	@ResponseBody
	public String oauthCallback(@RequestParam("code") String authCode, HttpServletResponse response) throws UserException {
		String accessToken = this.oauthService.requestAccessToken(authCode);
		ProfileResponseBody profileResponse = this.oauthService.requestOAuthProfile(accessToken);

		String userId = profileResponse.getComputedUserId();
		String userName = profileResponse.getComputedUserName();

		piazzaLogger.log(String.format("User %s with Name %s Successfully authenticated with OAuth provider.", userId, userName),
				Severity.INFORMATIONAL);

		UserProfile userProfile = this.oauthService.getOrCreateUser(userId, userName);

		String uiRedirectUri = UriComponentsBuilder.newInstance().scheme("https").host("beachfront." + this.domain).queryParam("logged_in", "true").build()
				.toUri().toString();

		response.addCookie(createCookie(userProfile.getApiKey(), COOKIE_EXPIRY_SECONDS));
		response.setStatus(HttpStatus.FOUND.value());
		response.setHeader("Location", uiRedirectUri);
		return "Authentication successful. Redirecting back to application...";
	}

	@RequestMapping(path = "/oauth/logout", method = RequestMethod.GET, produces = { "text/plain" })
	@ResponseBody
	public String oauthLogout(HttpServletResponse response, Authentication authentication) throws UserException {
		// Server-side invalidation of API Key
		UserProfile userProfile = userProfileService.getProfileFromAuthentication(authentication);
		this.piazzaLogger.log("User explicitly logged out, invalidating API key", Severity.INFORMATIONAL, 
				new AuditElement(userProfile.getName(), "logout", userProfile.getApiKey()));
		userProfileService.invalidateKey(userProfile);

		// Construct redirect url for server side logout
		final String uiUrl = "beachfront." + domain;
		// Forward user to server side logout
		String logoutRedirectUri = UriComponentsBuilder.fromUriString(oauthLogoutUrl).queryParam("end_url", uiUrl).build().toUri()
				.toString();

		// Clear the session cookie
		response.addCookie(createCookie(null, 0));
		response.setStatus(HttpStatus.OK.value());
		// TODO: Maybe we can change bf-ui to use a proper redirect?
		//response.setHeader("Location", logoutRedirectUri);
		return logoutRedirectUri;
	}

	private Cookie createCookie(String apiKey, int expiry) {
		Cookie cookie = new Cookie(COOKIE_NAME, apiKey);
		cookie.setDomain(domain);
		cookie.setSecure(true);
		cookie.setPath("/");
		cookie.setMaxAge(expiry);
		return cookie;
	}
}
