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

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

import javax.servlet.http.HttpServletResponse;

import org.joda.time.DateTime;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.test.util.ReflectionTestUtils;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.oauth.GeoAxisCommonName;
import org.venice.beachfront.bfapi.model.oauth.ProfileResponseBody;
import org.venice.beachfront.bfapi.services.OAuthService;
import org.venice.beachfront.bfapi.services.UserProfileService;

import util.PiazzaLogger;

public class OAuthControllerTests {
	@Mock
	private OAuthService oauthService;
	@Mock
	private UserProfileService userProfileService;
	@Mock
	private PiazzaLogger piazzaLogger;

	@InjectMocks
	private OAuthController oauthController;

	@Before
	public void setup() throws UserException {
		MockitoAnnotations.initMocks(this);

		ReflectionTestUtils.setField(oauthController, "domain", "localhost");
		ReflectionTestUtils.setField(oauthController, "oauthAuthorizeUrl", "http://authorize");
		ReflectionTestUtils.setField(oauthController, "oauthLogoutUrl", "http://logout");
		ReflectionTestUtils.setField(oauthController, "oauthClientId", "http://client");
		ReflectionTestUtils.setField(oauthController, "COOKIE_EXPIRY_SECONDS", 900);
		ReflectionTestUtils.setField(oauthController, "COOKIE_NAME", "api_key");
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
		ProfileResponseBody mockProfileResponse = new ProfileResponseBody("dn", new GeoAxisCommonName.SingleString("common"), "member", null, null, null);
		Mockito.doReturn(mockProfileResponse).when(oauthService).requestOAuthProfile(Mockito.eq(mockToken));
		UserProfile mockUserProfile = new UserProfile("userId", "userName", "apiKey", new DateTime());
		Mockito.doReturn(mockUserProfile).when(oauthService).getOrCreateUser(Mockito.eq(mockProfileResponse.getComputedUserId()),
				Mockito.eq(mockProfileResponse.getComputedUserName()));
		HttpServletResponse servletResponse = new MockHttpServletResponse();
		// Test
		String ack = oauthController.oauthCallback(mockAuthCode, servletResponse);
		assertNotNull(ack);
		assertEquals(servletResponse.getStatus(), HttpStatus.FOUND.value());
		assertEquals(servletResponse.getHeader("Location"), "https://beachfront.localhost?logged_in=true");
	}

	@Test
	public void testLogout() throws UserException {
		// Mock
		HttpServletResponse servletResponse = new MockHttpServletResponse();
		// Test
		String redirectUrl = oauthController.oauthLogout(servletResponse, null);
		assertEquals(servletResponse.getStatus(), HttpStatus.OK.value());
		assertEquals(redirectUrl, "http://logout?end_url=beachfront.localhost");
	}
}
