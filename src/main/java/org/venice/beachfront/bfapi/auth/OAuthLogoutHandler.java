package org.venice.beachfront.bfapi.auth;

import java.io.IOException;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.logout.LogoutHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.util.UriComponentsBuilder;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.UserProfileService;

@Component
public class OAuthLogoutHandler implements LogoutHandler {
	@Value("${DOMAIN}")
	private String domain;
	@Value("${cookie.name}")
	private String COOKIE_NAME;
	@Value("${oauth.logout-url}")
	private String oauthLogoutUrl;
	
	@Autowired
	private UserProfileService userProfileService;
	
	@Override
	public void logout(HttpServletRequest request, HttpServletResponse response, Authentication authentication) {
		try {
			this.logoutWithErrors(request, response, authentication);
		} catch (UserException e) {
			throw new RuntimeException(e);
		}
	}
	
	private void logoutWithErrors(HttpServletRequest request, HttpServletResponse response, Authentication authentication) throws UserException {
		UserProfile userProfile = userProfileService.getProfileFromAuthentication(authentication);
		if (userProfile == null) {
			throw new UserException("No authentication found to log out from", HttpStatus.UNAUTHORIZED);
		}
		// Server-side invalidation of API Key
		userProfileService.invalidateKey(userProfileService.getProfileFromAuthentication(authentication));

		// Clear the session cookie
		response.addCookie(createCookie(null, 0));
		response.setStatus(HttpStatus.OK.value());

		// Construct redirect url for server side logout
		final String uiUrl = "beachfront." + domain;
		// Forward user to server side logout
		String logoutRedirectUri = UriComponentsBuilder.fromUriString(oauthLogoutUrl).queryParam("end_url", uiUrl)
				.build().toUri().toString();

		// TODO: Maybe we can change bf-ui to use a proper redirect?
		try {
			response.getWriter().print(logoutRedirectUri);
		} catch (IOException e) {
			throw new UserException("Failed to write redirect URI", e, HttpStatus.INTERNAL_SERVER_ERROR);
		}
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
