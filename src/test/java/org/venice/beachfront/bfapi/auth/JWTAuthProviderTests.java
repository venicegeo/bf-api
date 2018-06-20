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
package org.venice.beachfront.bfapi.auth;

import org.joda.time.DateTime;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.mockito.Spy;
import org.springframework.security.core.Authentication;
import org.venice.beachfront.bfapi.auth.jwt.JWTAuthProvider;
import org.venice.beachfront.bfapi.auth.jwt.JWTToken;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.UserProfileService;

import com.fasterxml.jackson.databind.ObjectMapper;

import util.GeoAxisJWTUtility;
import util.PiazzaLogger;

/**
 * Testing JWT Authentication and Tokens
 * 
 * @author Patrick.Doody
 *
 */
public class JWTAuthProviderTests {
	@Mock
	private UserProfileService userProfileService;
	@Mock
	private PiazzaLogger piazzaLogger;
	@Spy
	private GeoAxisJWTUtility jwtUtility;
	@Spy
	private ObjectMapper objectMapper;
	@InjectMocks
	private JWTAuthProvider provider;

	private String VALID_NOT_EXPIRED = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2d4aXNhY2Nlc3MuY2kuZ3hhd3MuZGV2IiwiZXhwIjo5OTk5OTk5OTk5LCJzdWIiOiJUZXN0ZXIiLCJkbiI6IlRlc3RlciIsImNvb2tpZSI6IlZFUlNJT05fNX5jbk5DclN1RzVIWHVJTkFKL09KUmFBPT1-NUVkenVySDlOZXdFVVVpbG5NOEt6TGxYL0JMRHhMWDl0anBnYy91T1IzVlltTGhpU0g3QUc3c2UrOHRLUyt0OGdrcDZyOW0xc3dSNjcyWU5rclhFQzMxQmsyTG5TRDJnYjBhenN4L2h1amdUUkJENGZ0RE9qaUF2dlpEdlk5VGNtRm1MZXVPaWcwMCtKYW1PSisyVVAwVEVEWnhSZERPM3NBUWw4SHBNRTNVVzQyN0FwV1FFOW1XM2cxdEZVSnNCSmlkSVZTNXV3ZCtkaklZSjlNblpwd2FHMGdjcURBaDFWNldkaDgvRi9PMzFzSjl6ekswc3FjRHVtTEpubnFyS01zZzhjQUxqZHhpNmsvSW1FbGxNUEtmRnJFY0txUStpL1lXb3FLUGlRZzBkU2FoQVoyUmlvMFZzeWJtcTBBZHNBeHhwbVV5dk54M0dqNCtpcWpQb25IdWdrY0lvNDhidG5LOWl5QWRUQlc1cGNSemtuSzZyYXBCT3dod3NiZmFGWDZBeFBPbHpBdkhQbmFrdkxaandsS2p1d0gxSlphQ0ZPRDdHRkdCL1JaL2xMVTNHQWpZdmkyT1ZJK3NIWFpMd093VUgxMVNTRFBEY2RPbWVoT1JFZ1FHNnNCdEMxT3dNd2FWY3lFOVIxNVE9IiwianRpIjoiMzc3OTE2MzgtMGU1OC00ODI5LWJhNWItNjcyNWYyNjMwZjA5IiwiaWF0IjoxNTI5NDk4MzAzfQ.SWUxWS73e3bm7Oi5nY9Eegyw3NCELaWTzuITXAEAMSk";
	private String INVALID_EXPIRED = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2d4aXNhY2Nlc3MuY2kuZ3hhd3MuZGV2IiwiZXhwIjoxNTI5NTAxOTAzLCJzdWIiOiJUZXN0ZXIiLCJkbiI6IlRlc3RlciIsImNvb2tpZSI6IlZFUlNJT05fNX5jbk5DclN1RzVIWHVJTkFKL09KUmFBPT1-NUVkenVySDlOZXdFVVVpbG5NOEt6TGxYL0JMRHhMWDl0anBnYy91T1IzVlltTGhpU0g3QUc3c2UrOHRLUyt0OGdrcDZyOW0xc3dSNjcyWU5rclhFQzMxQmsyTG5TRDJnYjBhenN4L2h1amdUUkJENGZ0RE9qaUF2dlpEdlk5VGNtRm1MZXVPaWcwMCtKYW1PSisyVVAwVEVEWnhSZERPM3NBUWw4SHBNRTNVVzQyN0FwV1FFOW1XM2cxdEZVSnNCSmlkSVZTNXV3ZCtkaklZSjlNblpwd2FHMGdjcURBaDFWNldkaDgvRi9PMzFzSjl6ekswc3FjRHVtTEpubnFyS01zZzhjQUxqZHhpNmsvSW1FbGxNUEtmRnJFY0txUStpL1lXb3FLUGlRZzBkU2FoQVoyUmlvMFZzeWJtcTBBZHNBeHhwbVV5dk54M0dqNCtpcWpQb25IdWdrY0lvNDhidG5LOWl5QWRUQlc1cGNSemtuSzZyYXBCT3dod3NiZmFGWDZBeFBPbHpBdkhQbmFrdkxaandsS2p1d0gxSlphQ0ZPRDdHRkdCL1JaL2xMVTNHQWpZdmkyT1ZJK3NIWFpMd093VUgxMVNTRFBEY2RPbWVoT1JFZ1FHNnNCdEMxT3dNd2FWY3lFOVIxNVE9IiwianRpIjoiMzc3OTE2MzgtMGU1OC00ODI5LWJhNWItNjcyNWYyNjMwZjA5IiwiaWF0IjoxNTI5NDk4MzAzfQ.zBbmXgb0v-_9LpM81hxy2gSQGT47H1TiKpDWZ-jJRHM";
	private String INVALID_MISSING_DN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2d4aXNhY2Nlc3MuY2kuZ3hhd3MuZGV2IiwiZXhwIjoxNTI5NTAxOTE2LCJzdWIiOiJUZXN0ZXIiLCJjb29raWUiOiJWRVJTSU9OXzV-Y25OQ3JTdUc1SFh1SU5BSi9PSlJhQT09fjVFZHp1ckg5TmV3RVVVaWxuTThLekxsWC9CTER4TFg5dGpwZ2MvdU9SM1ZZbUxoaVNIN0FHN3NlKzh0S1MrdDhna3A2cjltMXN3UjY3MllOa3JYRUMzMUJrMkxuU0QyZ2IwYXpzeC9odWpnVFJCRDRmdERPamlBdnZaRHZZOVRjbUZtTGV1T2lnMDArSmFtT0orMlVQMFRFRFp4UmRETzNzQVFsOEhwTUUzVVc0MjdBcFdRRTltVzNnMXRGVUpzQkppZElWUzV1d2QrZGpJWUo5TW5acHdhRzBnY3FEQWgxVjZXZGg4L0YvTzMxc0o5enpLMHNxY0R1bUxKbm5xcktNc2c4Y0FMamR4aTZrL0ltRWxsTVBLZkZyRWNLcVEraS9ZV29xS1BpUWcwZFNhaEFaMlJpbzBWc3libXEwQWRzQXh4cG1VeXZOeDNHajQraXFqUG9uSHVna2NJbzQ4YnRuSzlpeUFkVEJXNXBjUnprbks2cmFwQk93aHdzYmZhRlg2QXhQT2x6QXZIUG5ha3ZMWmp3bEtqdXdIMUpaYUNGT0Q3R0ZHQi9SWi9sTFUzR0FqWXZpMk9WSStzSFhaTHdPd1VIMTFTU0RQRGNkT21laE9SRWdRRzZzQnRDMU93TXdhVmN5RTlSMTVRPSIsImp0aSI6IjM2ODgwYjFiLTQyMzQtNDg1My1hYTc2LTIxMjU3ZDI5M2E4MyIsImlhdCI6MTUyOTQ5ODMxNn0.3MsZ75eHKZ2uTXXcZkAddpfn79zif7yCmKn7Ge3zqf4";
	private String INVALID_MISSING_EXP = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2d4aXNhY2Nlc3MuY2kuZ3hhd3MuZGV2Iiwic3ViIjoiVGVzdGVyIiwiY29va2llIjoiVkVSU0lPTl81fmNuTkNyU3VHNUhYdUlOQUovT0pSYUE9PX41RWR6dXJIOU5ld0VVVWlsbk04S3pMbFgvQkxEeExYOXRqcGdjL3VPUjNWWW1MaGlTSDdBRzdzZSs4dEtTK3Q4Z2twNnI5bTFzd1I2NzJZTmtyWEVDMzFCazJMblNEMmdiMGF6c3gvaHVqZ1RSQkQ0ZnRET2ppQXZ2WkR2WTlUY21GbUxldU9pZzAwK0phbU9KKzJVUDBURURaeFJkRE8zc0FRbDhIcE1FM1VXNDI3QXBXUUU5bVczZzF0RlVKc0JKaWRJVlM1dXdkK2RqSVlKOU1uWnB3YUcwZ2NxREFoMVY2V2RoOC9GL08zMXNKOXp6SzBzcWNEdW1MSm5ucXJLTXNnOGNBTGpkeGk2ay9JbUVsbE1QS2ZGckVjS3FRK2kvWVdvcUtQaVFnMGRTYWhBWjJSaW8wVnN5Ym1xMEFkc0F4eHBtVXl2TngzR2o0K2lxalBvbkh1Z2tjSW80OGJ0bks5aXlBZFRCVzVwY1J6a25LNnJhcEJPd2h3c2JmYUZYNkF4UE9sekF2SFBuYWt2TFpqd2xLanV3SDFKWmFDRk9EN0dGR0IvUlovbExVM0dBall2aTJPVkkrc0hYWkx3T3dVSDExU1NEUERjZE9tZWhPUkVnUUc2c0J0QzFPd013YVZjeUU5UjE1UT0iLCJqdGkiOiJiYmEwNzgzMy02ODExLTQ0ZGQtOWNmMi0yNDMyZTUyZjFjYzIiLCJpYXQiOjE1Mjk0OTgzNDIsImV4cCI6MTUyOTUwMTk0Mn0.gitdSloPFzm2GorOQ6pGg_7rur2abksgQW92GRcWdcM";

	@Before
	public void setup() {
		MockitoAnnotations.initMocks(this);
	}

	/**
	 * Tests JWT Token serialization
	 */
	@Test
	public void testJwtToken() {
		String tokenName = "token";
		JWTToken token = new JWTToken(tokenName);

		Assert.assertEquals(token.getPrincipal(), tokenName);
		Assert.assertNull(token.getCredentials());
	}

	/**
	 * Test when the utility returns an invalid signature
	 */
	@Test
	public void testInvalidSignature() {
		// Mock
		Mockito.when(jwtUtility.isJWTValid(Mockito.anyString())).thenReturn(false);
		// Test
		Authentication result = provider.authenticate(new JWTToken(VALID_NOT_EXPIRED));
		Assert.assertNull(result);
	}

	/**
	 * Test various JWTs against the provider for expected results
	 */
	@Test
	public void testAuthentication() {
		// Mock
		Mockito.when(jwtUtility.isJWTValid(Mockito.anyString())).thenReturn(true);

		// Test an Expired JWT
		Authentication result = provider.authenticate(new JWTToken(INVALID_EXPIRED));
		Assert.assertNull(result);

		// Test a JWT without a DN
		result = provider.authenticate(new JWTToken(INVALID_MISSING_DN));
		Assert.assertNull(result);

		// Test a JWT without an Expiration date
		result = provider.authenticate(new JWTToken(INVALID_MISSING_EXP));
		Assert.assertNull(result);

		// Test a successful non-expired JWT with a non-defined User Profile
		result = provider.authenticate(new JWTToken(VALID_NOT_EXPIRED));
		Assert.assertNull(result);

		// Test a successful non-expired JWT with a valid User Profile
		Mockito.when(userProfileService.getUserProfileById("Tester"))
				.thenReturn(new UserProfile("Tester", "Tester", "Test", DateTime.now()));
		result = provider.authenticate(new JWTToken(VALID_NOT_EXPIRED));
		Assert.assertNotNull(result);
		Assert.assertTrue(result instanceof BfAuthenticationToken);
		BfAuthenticationToken bfToken = (BfAuthenticationToken) result;
		Assert.assertTrue(bfToken.getPrincipal() instanceof UserProfile);
		Assert.assertEquals(((UserProfile) bfToken.getPrincipal()).getUserId(), "Tester");
	}

}
