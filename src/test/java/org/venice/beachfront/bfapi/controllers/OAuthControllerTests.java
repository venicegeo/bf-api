package org.venice.beachfront.bfapi.controllers;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import org.joda.time.DateTime;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.util.ReflectionTestUtils;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.oauth.ProfileResponseBody;
import org.venice.beachfront.bfapi.services.OAuthService;

public class OAuthControllerTests {
	@Mock
	private OAuthService oauthService;
	@InjectMocks
	private OAuthController oauthController;

	@Before
	public void setup() throws UserException {
		MockitoAnnotations.initMocks(this);

		ReflectionTestUtils.setField(oauthController, "domain", "localhost");
		ReflectionTestUtils.setField(oauthController, "oauthAuthorizeUrl", "http://authorize");
		ReflectionTestUtils.setField(oauthController, "oauthLogoutUrl", "http://logout");
		ReflectionTestUtils.setField(oauthController, "oauthClientId", "http://client");
	}

	@Test
	public void testStartExchange() {
		// Mock
		Mockito.doReturn("callback").when(oauthService).getOauthRedirectUri();
		HttpServletResponse servletResponse = new MockHttpServletResponse();
		// Test
		String ack = oauthController.oauthStartExchange(servletResponse);
		assertNotNull(ack);
		assertEquals(servletResponse.getStatus(), HttpStatus.FOUND.value());
		assertEquals(servletResponse.getHeader("Location"),
				"http://authorize?client_id=http://client&redirect_uri=callback&response_type=code&scope=UserProfile.me");
	}

	@Test
	public void testCallback() throws UserException {
		// Mock
		String mockAuthCode = "mockAuthCode";
		String mockToken = "mockToken";
		Mockito.doReturn(mockToken).when(oauthService).requestAccessToken(Mockito.eq(mockAuthCode));
		ProfileResponseBody mockProfileResponse = new ProfileResponseBody("dn", "common", "member");
		Mockito.doReturn(mockProfileResponse).when(oauthService).requestOAuthProfile(Mockito.eq(mockToken));
		UserProfile mockUserProfile = new UserProfile("userId", "userName", "apiKey", new DateTime());
		Mockito.doReturn(mockUserProfile).when(oauthService).getOrCreateUser(Mockito.eq(mockProfileResponse.getComputedUserId()),
				Mockito.eq(mockProfileResponse.getComputedUserName()));
		HttpServletResponse servletResponse = new MockHttpServletResponse();
		HttpSession session = new MockHttpSession();
		// Test
		String ack = oauthController.oauthCallback(mockAuthCode, session, servletResponse);
		assertNotNull(ack);
		assertEquals(session.getAttribute("api_key"), mockUserProfile.getApiKey());
		assertEquals(servletResponse.getStatus(), HttpStatus.FOUND.value());
		assertEquals(servletResponse.getHeader("Location"), "https://localhost?logged_in=true");
	}
	
	@Test
	public void testLogout() throws UserException {
		// Mock
		HttpServletResponse servletResponse = new MockHttpServletResponse();
		HttpSession session = new MockHttpSession();
		// Test
		String ack = oauthController.oauthLogout(session, servletResponse);
		assertNotNull(ack);
		assertEquals(servletResponse.getStatus(), HttpStatus.FOUND.value());
		System.out.println(servletResponse.getHeader("Location"));
		// TODO: Fails
		assertEquals(servletResponse.getHeader("Location"), "https://localhost?end_url=true");
	}
}
