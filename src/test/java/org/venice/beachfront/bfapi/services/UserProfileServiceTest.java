package org.venice.beachfront.bfapi.services;

import java.util.ArrayList;

import org.joda.time.DateTime;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Matchers;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.core.env.Environment;
import org.springframework.security.core.Authentication;
import org.springframework.test.util.ReflectionTestUtils;
import org.venice.beachfront.bfapi.database.dao.UserProfileDao;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;

import util.PiazzaLogger;

public class UserProfileServiceTest {

    @Mock
    UserProfileDao userProfileDao;
    @Mock
    PiazzaLogger piazzaLogger;
    @Mock
    Environment environment;

    @InjectMocks
    UserProfileService userProfileService;

    @Before
    public void setup() {
        MockitoAnnotations.initMocks(this);

        ReflectionTestUtils.setField(this.userProfileService, "API_KEY_TIMEOUT_MINUTES", 10);
    }

    @Test
    public void saveUserProfile() {
        this.userProfileService.saveUserProfile(new UserProfile());
        Mockito.verify(this.userProfileDao, Mockito.times(1)).save(Matchers.any(UserProfile.class));
    }

    @Test
    public void updateLastAccessed() {
        this.userProfileService.updateLastAccessed(new UserProfile());
        Mockito.verify(this.userProfileDao, Mockito.times(1)).save(Matchers.any(UserProfile.class));
    }

    @Test
    public void invalidateKey() {
        this.userProfileService.invalidateKey(new UserProfile());
        Mockito.verify(this.userProfileDao, Mockito.times(1)).save(Matchers.any(UserProfile.class));
    }

    @Test
    public void getProfileFromAuthentication() throws Exception {
        Authentication auth = Mockito.mock(Authentication.class);
        Mockito.when(environment.getActiveProfiles()).thenReturn(new String[]{"cloud", "secure", "test"});

        Mockito.when(auth.getPrincipal())
                .thenReturn(new UserProfile())
                .thenThrow(Exception.class);

        Assert.assertNotNull(this.userProfileService.getProfileFromAuthentication(auth));

        try {
            this.userProfileService.getProfileFromAuthentication(auth);
            Assert.fail("Expected a UserException");
        } catch (UserException ex) {
        }
    }

    @Test
    public void reapExpiredApiKeys() {
        ArrayList<UserProfile> profilesList = new ArrayList<>();
        profilesList.add(new UserProfile());
        profilesList.add(new UserProfile());

        profilesList.get(0).setLastAccessed(DateTime.now());
        profilesList.get(0).setApiKey("key_1");
        profilesList.get(1).setLastAccessed(DateTime.now().minusDays(1));
        profilesList.get(1).setApiKey("key_2");

        Mockito.when(this.userProfileDao.findAll())
                .thenReturn(profilesList);

        this.userProfileService.reapExpiredApiKeys();

        //The key for the valid profile should be unchanged.
        Assert.assertNotNull(profilesList.get(0).getApiKey());

        //The key for the expired profile should be nullified.
        Assert.assertNull(profilesList.get(1).getApiKey());
    }
}