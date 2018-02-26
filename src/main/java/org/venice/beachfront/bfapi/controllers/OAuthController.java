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

	@Autowired
	private OAuthService oauthService;

	@Autowired
	private UserProfileService userProfileService;

	@RequestMapping(path = "/login/geoaxis", method = RequestMethod.GET, produces = { "text/plain" })
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

	@RequestMapping(path = "/login", method = RequestMethod.GET, produces = { "text/plain" })
	@ResponseBody
	public String oauthCallback(@RequestParam("code") String authCode, HttpServletResponse response) throws UserException {
		String accessToken = this.oauthService.requestAccessToken(authCode);
		ProfileResponseBody profileResponse = this.oauthService.requestOAuthProfile(accessToken);

		String userId = profileResponse.getComputedUserId();
		String userName = profileResponse.getComputedUserName();

		UserProfile userProfile = this.oauthService.getOrCreateUser(userId, userName);

		String uiRedirectUri = UriComponentsBuilder.newInstance().scheme("https").host(this.domain).queryParam("logged_in", "true").build()
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
		userProfileService.invalidateKey(userProfileService.getProfileFromAuthentication(authentication));

		// Construct redirect url for server side logout
		final String uiUrl = "beachfront." + domain;
		// Forward user to server side logout
		String logoutRedirectUri = UriComponentsBuilder.fromUriString(oauthLogoutUrl).queryParam("end_url", uiUrl).build().toUri()
				.toString();

		// Clear the session cookie
		response.addCookie(createCookie(null, 0));
		response.setStatus(HttpStatus.FOUND.value());
		response.setHeader("Location", logoutRedirectUri);
		return "Logging out. Redirecting to oauth logout...";
	}

	private Cookie createCookie(String apiKey, int expiry) {
		Cookie cookie = new Cookie("api_key", apiKey);
		cookie.setDomain(String.format("*.%s", domain));
		cookie.setSecure(true);
		cookie.setPath("/");
		cookie.setMaxAge(expiry);
		return cookie;
	}
}
