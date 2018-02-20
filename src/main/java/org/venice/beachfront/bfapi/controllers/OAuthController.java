package org.venice.beachfront.bfapi.controllers;

import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.util.UriComponentsBuilder;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.oauth.ProfileResponseBody;
import org.venice.beachfront.bfapi.services.OAuthService;

public class OAuthController {
	@Value("${DOMAIN}")
	private String domain;

	@Value("${oauth.authorize-url}")
	private String oauthAuthorizeUrl;

	@Value("${oauth.client-id}")
	private String oauthClientId;

	@Autowired
	private OAuthService oauthService;

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
	public String oauthCallback(@RequestParam("code") String authCode, HttpSession session, HttpServletResponse response)
			throws UserException {
		String accessToken = this.oauthService.requestAccessToken(authCode);
		ProfileResponseBody profileResponse = this.oauthService.requestOAuthProfile(accessToken);

		String userId = profileResponse.getComputedUserId();
		String userName = profileResponse.getComputedUserName();

		UserProfile userProfile = this.oauthService.getOrCreateUser(userId, userName);

		String uiRedirectUri = UriComponentsBuilder.newInstance().scheme("https").host(this.domain).queryParam("logged_in", "true").build()
				.toUri().toString();

		session.setAttribute("api_key", userProfile.getApiKey());
		response.setStatus(HttpStatus.FOUND.value());
		response.setHeader("Location", uiRedirectUri);
		return "Authentication successful. Redirecting back to application...";
	}

}
