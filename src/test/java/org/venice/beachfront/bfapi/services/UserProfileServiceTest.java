package org.venice.beachfront.bfapi.services;

import org.joda.time.DateTime;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.springframework.security.core.Authentication;
import org.springframework.test.util.ReflectionTestUtils;
import org.venice.beachfront.bfapi.database.dao.UserProfileDao;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import util.PiazzaLogger;

import java.util.ArrayList;

public class UserProfileServiceTest {

    @Mock
    UserProfileDao userProfileDao;
    @Mock
    PiazzaLogger piazzaLogger;

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
    }

    @Test
    public void getUserProfileById() {

    }

    @Test
    public void getUserProfileByApiKey() {
    }

    @Test
    public void updateLastAccessed() {
        this.userProfileService.updateLastAccessed(new UserProfile());
    }

    @Test
    public void invalidateKey() {
        this.userProfileService.invalidateKey(new UserProfile());
    }

    @Test(expected = UserException.class)
    public void getProfileFromAuthentication() throws Exception {
        Authentication auth = Mockito.mock(Authentication.class);

        Mockito.when(auth.getPrincipal())
                .thenReturn(new UserProfile())
                .thenThrow(Exception.class);

        this.userProfileService.getProfileFromAuthentication(auth);
        this.userProfileService.getProfileFromAuthentication(auth);
    }

    @Test
    public void reapExpiredApiKeys() {
        ArrayList<UserProfile> profilesList = new ArrayList<>();
        profilesList.add(new UserProfile());
        profilesList.add(new UserProfile());

        profilesList.get(0).setLastAccessed(DateTime.now());
        profilesList.get(1).setLastAccessed(DateTime.now().minusDays(1));

        Mockito.when(this.userProfileDao.findAll())
                .thenReturn(profilesList);

        this.userProfileService.reapExpiredApiKeys();
    }
}