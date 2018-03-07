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

import util.PiazzaLogger;

public class UserProfileControllerTests {
	@Mock
	private UserProfileService userProfileService;
	@Mock
	private PiazzaLogger piazzaLogger;
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
