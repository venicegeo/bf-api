package org.venice.beachfront.bfapi.auth;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.io.UnsupportedEncodingException;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.log4j.Logger;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.mockito.invocation.InvocationOnMock;
import org.mockito.stubbing.Answer;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.core.Authentication;
import org.springframework.test.util.ReflectionTestUtils;
import org.venice.beachfront.bfapi.controllers.OAuthController;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.OAuthService;
import org.venice.beachfront.bfapi.services.UserProfileService;

import util.PiazzaLogger;

public class OAuthLogoutHandlerTests {
	@Mock
	private UserProfileService userProfileService;
	
	@Mock
	private Logger logger;

	@InjectMocks
	private OAuthLogoutHandler oauthLogoutHandler;

	@Before
	public void setup() throws UserException {
		MockitoAnnotations.initMocks(this);

		ReflectionTestUtils.setField(oauthLogoutHandler, "domain", "test.localdomain");
		ReflectionTestUtils.setField(oauthLogoutHandler, "COOKIE_NAME", "test_api_key");
		ReflectionTestUtils.setField(oauthLogoutHandler, "oauthLogoutUrl", "http://mock-oauth.localdomain/logout");
	}
	
	@Test
	public void testLogoutSuccess() throws UserException, UnsupportedEncodingException {
		// Mock
		MockHttpServletRequest request = new MockHttpServletRequest();
		MockHttpServletResponse response = new MockHttpServletResponse();
		Authentication authentication = Mockito.mock(Authentication.class);
		UserProfile userProfile = Mockito.mock(UserProfile.class);
		
		final boolean[] userProfileInvalidated = {false};
		
		Mockito.when(this.userProfileService.getProfileFromAuthentication(authentication)).thenReturn(userProfile);
		Mockito.doAnswer(new Answer<Object>() {
			@Override
			public Object answer(InvocationOnMock invocation) throws Throwable {
				userProfileInvalidated[0] = true;
				return null;
		}}).when(this.userProfileService).invalidateKey(Mockito.same(userProfile));
		
		// Test
		this.oauthLogoutHandler.logout(request, response, authentication);
		
		assertTrue(userProfileInvalidated[0]);
		assertEquals(response.getStatus(), HttpStatus.OK.value());
		assertEquals("http://mock-oauth.localdomain/logout?end_url=beachfront.test.localdomain", response.getContentAsString());
	}
	
	@Test
	public void testLogoutNotAuthenticated() throws UserException, UnsupportedEncodingException {
		// Mock
		MockHttpServletRequest request = new MockHttpServletRequest();
		MockHttpServletResponse response = new MockHttpServletResponse();
		Authentication authentication = Mockito.mock(Authentication.class);
				
		Mockito.when(this.userProfileService.getProfileFromAuthentication(authentication)).thenReturn(null);
		
		// Test
		this.oauthLogoutHandler.logout(request, response, authentication);
		
		assertEquals(HttpStatus.UNAUTHORIZED.value(), response.getStatus());			
	}
}
