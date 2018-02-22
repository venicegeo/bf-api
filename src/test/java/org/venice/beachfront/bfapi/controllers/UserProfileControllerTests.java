package org.venice.beachfront.bfapi.controllers;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

import org.joda.time.DateTime;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.venice.beachfront.bfapi.model.UserProfile;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.UserProfileService;

public class UserProfileControllerTests {
	@Mock
	private UserProfileService userProfileService;
	@InjectMocks
	private UserProfileController userProfileController;

	@Before
	public void setup() throws UserException {
		MockitoAnnotations.initMocks(this);
	}

	@Test
	public void testGetProfile() throws UserException {
		// Mock
		UserProfile mockProfile = new UserProfile("Tester", "Tester", "Key", new DateTime());
		Mockito.doReturn(mockProfile).when(userProfileService).getProfileFromAuthentication(Mockito.any());
		// Test
		UserProfile userProfile = userProfileController.getCurrentUserProfile(null);
		assertNotNull(userProfile);
		assertEquals(userProfile.getName(), mockProfile.getName());
	}

	@Test(expected = UserException.class)
	public void testProfileError() throws UserException {
		userProfileController.getCurrentUserProfile(null);
	}
}
