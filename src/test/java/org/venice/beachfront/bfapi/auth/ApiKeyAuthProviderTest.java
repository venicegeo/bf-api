package org.venice.beachfront.bfapi.auth;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.security.core.Authentication;
import org.springframework.test.util.ReflectionTestUtils;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.services.UserProfileService;
import org.w3.xlink.Extended;
import util.PiazzaLogger;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;

import static org.junit.Assert.*;

public class ApiKeyAuthProviderTest {

    @Mock
    UserProfileService userProfileService;
    @Mock
    PiazzaLogger piazzaLogger;

    @InjectMocks
    ApiKeyAuthProvider apiKeyAuthProvider;

    @Before
    public void setup() {
        MockitoAnnotations.initMocks(this);

        ReflectionTestUtils.setField(this.apiKeyAuthProvider, "COOKIE_NAME", "api_key");
    }

    @Test
    public void authenticate() {
        Authentication auth = Mockito.mock(Authentication.class);
        MockHttpServletRequest servletRequest = new MockHttpServletRequest();
        ExtendedRequestDetails reqDetails = new ExtendedRequestDetails(servletRequest);
        servletRequest.setCookies(new Cookie[] {new Cookie("api_key", "my_api_key")});

        Mockito.when(userProfileService.getUserProfileByApiKey("my_api_key"))
                .thenReturn(new UserProfile())
                .thenReturn(null);

        Mockito.when(auth.getDetails()).thenReturn(reqDetails);

        Assert.assertNotNull(apiKeyAuthProvider.authenticate(auth));
        Assert.assertNull(apiKeyAuthProvider.authenticate(auth));
    }
}