package org.venice.beachfront.bfapi.services;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.Before;
import org.junit.Ignore;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.mockito.invocation.InvocationOnMock;
import org.mockito.stubbing.Answer;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.model.oauth.AccessTokenRequestBody;
import org.venice.beachfront.bfapi.model.oauth.AccessTokenResponseBody;
import org.venice.beachfront.bfapi.model.oauth.ProfileResponseBody;

import util.PiazzaLogger;

public class OAuthServiceTests {
	@Mock
	private RestTemplate restTemplate;
	@Mock
	private UserProfileService userProfileService;
	@Mock
	private PiazzaLogger piazzaLogger;
	@InjectMocks
	private OAuthService oauthService;

	private String oauthTokenUrl = "https://oauth-test.localdomain/token";
	private String oauthProfileUrl = "https://oauth-test.localdomain/profile";
	private String oauthClientId = "TEST_CLIENT_ID";
	private String oauthClientSecret = "TEST_CLIENT_SECRET";

	@Before
	public void setup() {
		MockitoAnnotations.initMocks(this);

		ReflectionTestUtils.setField(this.oauthService, "domain", "test.localdomain");
		ReflectionTestUtils.setField(this.oauthService, "oauthTokenUrl", this.oauthTokenUrl);
		ReflectionTestUtils.setField(this.oauthService, "oauthProfileUrl", this.oauthProfileUrl);
		ReflectionTestUtils.setField(this.oauthService, "oauthClientId", this.oauthClientId);
		ReflectionTestUtils.setField(this.oauthService, "oauthClientSecret", this.oauthClientSecret);
	}

	@Test
	public void testGetOauthRedirectUri() {
		String uri = this.oauthService.getOauthRedirectUri();
		assertEquals("//bf-api.test.localdomain/login", uri);
	}

	@Test
	@Ignore
	// TODO: Filip this test is breaking
	public void testRequestAccessTokenSuccess() throws UserException {
		String mockAuthCode = "mock-auth-code-123";
		String mockAccessToken = "mock-access-token-321";

		AccessTokenResponseBody mockResponse = Mockito.mock(AccessTokenResponseBody.class);
		Mockito.when(mockResponse.getAccessToken()).thenReturn(mockAccessToken);

		Mockito.when(this.restTemplate.exchange(Mockito.eq(this.oauthTokenUrl), Mockito.eq(HttpMethod.POST), Mockito.any(),
				Mockito.eq(AccessTokenResponseBody.class))).then(new Answer<ResponseEntity<AccessTokenResponseBody>>() {
					@Override
					public ResponseEntity<AccessTokenResponseBody> answer(InvocationOnMock invocation) {
						HttpEntity<AccessTokenRequestBody> entity = invocation.getArgumentAt(2, HttpEntity.class);
						AccessTokenRequestBody body = entity.getBody();
						assertEquals(mockAuthCode, body.getCode());
						assertEquals("authorization_code", body.getGrantType());
						assertEquals(oauthService.getOauthRedirectUri(), body.getRedirectUri());
						return new ResponseEntity<AccessTokenResponseBody>(mockResponse, HttpStatus.OK);
					}
				});

		String receivedAccessToken = this.oauthService.requestAccessToken(mockAuthCode);
		assertEquals(mockAccessToken, receivedAccessToken);
	}

	@Test
	public void testRequestAccessTokenUserError() {
		String mockAuthCode = "mock-auth-code-123";

		Mockito.when(this.restTemplate.exchange(Mockito.eq(this.oauthTokenUrl), Mockito.eq(HttpMethod.POST), Mockito.any(),
				Mockito.eq(AccessTokenResponseBody.class))).then(new Answer<ResponseEntity<AccessTokenResponseBody>>() {
					@Override
					public ResponseEntity<AccessTokenResponseBody> answer(InvocationOnMock invocation) {
						throw new HttpClientErrorException(HttpStatus.UNAUTHORIZED);
					}
				});

		try {
			oauthService.requestAccessToken(mockAuthCode);
			fail("request should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.UNAUTHORIZED, ex.getRecommendedStatusCode());
		}
	}

	@Test
	public void testRequestAccessTokenServerError() {
		String mockAuthCode = "mock-auth-code-123";

		Mockito.when(this.restTemplate.exchange(Mockito.eq(this.oauthTokenUrl), Mockito.eq(HttpMethod.POST), Mockito.any(),
				Mockito.eq(AccessTokenResponseBody.class))).then(new Answer<ResponseEntity<AccessTokenResponseBody>>() {
					@Override
					public ResponseEntity<AccessTokenResponseBody> answer(InvocationOnMock invocation) {
						throw new HttpServerErrorException(HttpStatus.GATEWAY_TIMEOUT);
					}
				});

		try {
			oauthService.requestAccessToken(mockAuthCode);
			fail("request should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.BAD_GATEWAY, ex.getRecommendedStatusCode());
			assertTrue(ex.getMessage().contains("" + HttpStatus.GATEWAY_TIMEOUT.value()));
		}
	}

	@Test
	public void testRequestOAuthProfileSuccess() throws UserException {
		String mockAccessToken = "mock-access-token-321";
		ProfileResponseBody mockResponseBody = new ProfileResponseBody("test-dn", mockAccessToken, "test-member-of");

		Mockito.when(this.restTemplate.exchange(Mockito.eq(this.oauthProfileUrl), Mockito.eq(HttpMethod.GET), Mockito.any(),
				Mockito.eq(ProfileResponseBody.class))).then(new Answer<ResponseEntity<ProfileResponseBody>>() {
					@Override
					public ResponseEntity<ProfileResponseBody> answer(InvocationOnMock invocation) {
						HttpEntity<?> entity = invocation.getArgumentAt(2, HttpEntity.class);
						List<String> headerValues = entity.getHeaders().get("Authorization");
						assertEquals(1, headerValues.size());
						assertEquals("Bearer " + mockAccessToken, headerValues.get(0));
						return new ResponseEntity<>(mockResponseBody, HttpStatus.OK);
					}
				});

		ProfileResponseBody receivedResponseBody = this.oauthService.requestOAuthProfile(mockAccessToken);

		assertSame(mockResponseBody, receivedResponseBody);
	}

	@Test
	public void testRequestOAuthProfileUserError() {
		String mockAccessToken = "mock-access-token-321";

		Mockito.when(this.restTemplate.exchange(Mockito.eq(this.oauthProfileUrl), Mockito.eq(HttpMethod.GET), Mockito.any(),
				Mockito.eq(ProfileResponseBody.class))).then(new Answer<ResponseEntity<ProfileResponseBody>>() {
					@Override
					public ResponseEntity<ProfileResponseBody> answer(InvocationOnMock invocation) {
						throw new HttpClientErrorException(HttpStatus.UNAUTHORIZED);
					}
				});

		try {
			oauthService.requestOAuthProfile(mockAccessToken);
			fail("request should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.UNAUTHORIZED, ex.getRecommendedStatusCode());
		}
	}

	@Test
	public void testRequestOAuthProfileServerError() {
		String mockAccessToken = "mock-access-token-321";

		Mockito.when(this.restTemplate.exchange(Mockito.eq(this.oauthProfileUrl), Mockito.eq(HttpMethod.GET), Mockito.any(),
				Mockito.eq(ProfileResponseBody.class))).then(new Answer<ResponseEntity<ProfileResponseBody>>() {
					@Override
					public ResponseEntity<ProfileResponseBody> answer(InvocationOnMock invocation) {
						throw new HttpServerErrorException(HttpStatus.GATEWAY_TIMEOUT);
					}
				});

		try {
			oauthService.requestOAuthProfile(mockAccessToken);
			fail("request should not have succeeded");
		} catch (UserException ex) {
			assertEquals(HttpStatus.BAD_GATEWAY, ex.getRecommendedStatusCode());
			assertTrue(ex.getMessage().contains("" + HttpStatus.GATEWAY_TIMEOUT.value()));
		}
	}

	@Test
	public void testGetExistingUserWithApiKey() {
		String mockUserId = "test-user-id";
		String mockUserName = "test-user-name";
		String mockApiKey = "test-api-key";

		UserProfile mockUserProfile = Mockito.mock(UserProfile.class);
		Mockito.when(mockUserProfile.getApiKey()).thenReturn(mockApiKey);
		Mockito.doAnswer(new Answer<Object>() {
			@Override
			public Object answer(InvocationOnMock invocation) {
				fail("should not be setting a new api key on the found user");
				return null;
			}
		}).when(mockUserProfile).setApiKey(Mockito.anyString());

		Mockito.when(this.userProfileService.getUserProfileById(mockUserId)).thenReturn(mockUserProfile);

		UserProfile retrievedUser = this.oauthService.getOrCreateUser(mockUserId, mockUserName);

		assertSame(mockUserProfile, retrievedUser);
	}

	@Test
	public void testGetExistingUserWithoutApiKey() {
		String mockUserId = "test-user-id";
		String mockUserName = "test-user-name";

		final Map<String, Boolean> sideEffects = new HashMap<>();
		sideEffects.put("apiKeyUpdated", false);
		sideEffects.put("userAccessUpdated", false);

		UserProfile mockUserProfile = Mockito.mock(UserProfile.class);
		Mockito.when(mockUserProfile.getApiKey()).thenReturn(null);
		Mockito.doAnswer(new Answer<Object>() {
			@Override
			public Object answer(InvocationOnMock invocation) {
				sideEffects.put("apiKeyUpdated", true);
				return null;
			}
		}).when(mockUserProfile).setApiKey(Mockito.anyString());

		Mockito.when(this.userProfileService.getUserProfileById(mockUserId)).thenReturn(mockUserProfile);
		Mockito.doAnswer(new Answer<Object>() {
			@Override
			public Object answer(InvocationOnMock invocation) {
				sideEffects.put("userAccessUpdated", true);
				return null;
			}
		}).when(this.userProfileService).updateLastAccessed(mockUserProfile);

		UserProfile retrievedUser = this.oauthService.getOrCreateUser(mockUserId, mockUserName);

		assertSame(mockUserProfile, retrievedUser);
		assertTrue(sideEffects.get("apiKeyUpdated"));
		assertTrue(sideEffects.get("userAccessUpdated"));
	}

	@Test
	public void testCreateUser() {
		String mockUserId = "test-user-id";
		String mockUserName = "test-user-name";

		final List<UserProfile> mockUserDb = new ArrayList<>();

		Mockito.when(this.userProfileService.getUserProfileById(mockUserId)).thenReturn(null);
		Mockito.doAnswer(new Answer<Object>() {
			@Override
			public Object answer(InvocationOnMock invocation) {
				UserProfile savedUserProfile = invocation.getArgumentAt(0, UserProfile.class);
				mockUserDb.add(savedUserProfile);
				return null;
			}
		}).when(this.userProfileService).saveUserProfile(Mockito.any(UserProfile.class));
		;

		UserProfile retrievedUser = this.oauthService.getOrCreateUser(mockUserId, mockUserName);

		assertEquals(1, mockUserDb.size());
		UserProfile savedUser = mockUserDb.get(0);

		assertSame(savedUser, retrievedUser);
		assertEquals(mockUserId, retrievedUser.getUserId());
		assertEquals(mockUserName, retrievedUser.getName());
	}
}
